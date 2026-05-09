"""Offer generation pipeline: embed → retrieve → Claude → persist.

Single entry point: `generate_offer(request, user_id, session)`. The flow is:

  1. Build a query string from the discovery transcript + structured fields,
     embed it with Voyage (input_type="query").
  2. Cosine-retrieve top-K Bestandsangebote from `offer_embeddings`.
  3. Send Claude an Anthropic tool-use call whose schema is the Pydantic
     `OfferContent` model — Claude must reply via `submit_offer`.
  4. Persist a new Offer (status=draft) with OfferVersion v1.

We do NOT create an embedding for the new offer here. The few-shot pool only
contains validated historical offers; newly drafted ones will be promoted by a
later endpoint when the user marks them won.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from anthropic.types import ToolUseBlock
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Offer, OfferVersion
from app.schemas.offer import OfferContent, OfferGenerateRequest, OfferGenerateResponse
from app.services.embeddings import embed_text
from app.services.llm import get_anthropic_client
from app.services.retrieval import RetrievedOffer, retrieve_similar_offers

settings = get_settings()

DEFAULT_K = 3
# 8192 leaves comfortable headroom for full OfferContent JSON. At 4096 Claude
# was getting cut mid-tool-call and returned partial JSON with literal
# `$PARAMETER_NAME` placeholder keys, which then failed Pydantic validation.
MAX_OUTPUT_TOKENS = 8192

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_SKELETON_PATH = _PROMPTS_DIR / "offer_skeleton.md"

SYSTEM_INSTRUCTIONS = """Du bist ein Senior-Berater der ERA Group und schreibst Angebote für Beratungs-Mandate auf Deutsch.

Aufgabe: Aus einem Discovery-Call-Transkript, den User-Anmerkungen und einem Preis erstellst du ein strukturiertes Angebot. Dafür dienen dir bestehende Angebote als Stil- und Struktur-Referenz.

Anforderungen an Tonfall und Inhalt:
- Sprache: Deutsch, Sie-Form, professionell-direkt, partnerschaftlich.
- Inhalt: konkret, sachlich, an den im Transkript genannten Pain-Points orientiert. Kein Marketing-Fluff.
- Bestandteile: 2 bis 5 Stück, jeder mit klarer thematischer Abgrenzung.
- Investition: kommuniziere den Preis als Festpreis exklusive MwSt., mit kurzer Begründung des Mehrwerts.
- Rahmenbedingungen: Standard-Sätze zu Zahlungsziel, Vertraulichkeit, Geltungsdauer.

Struktur und Output: Antworte ausschließlich über den `submit_offer`-Tool-Call mit dem geforderten JSON-Schema. Kein erklärender Text außerhalb des Tool-Calls."""


def _load_skeleton() -> str:
    return _SKELETON_PATH.read_text(encoding="utf-8")


def _build_query_text(request: OfferGenerateRequest) -> str:
    """Compose the input text for the Voyage embedding (query side).

    Mirrors the shape of the seed summaries so cosine distance is meaningful.
    """
    parts = [
        f"Kunde: {request.client_name}",
        f"Branche: {request.industry or 'unbekannt'}",
        f"Beratungsart: {request.consulting_type}",
        f"Preis: {request.price_eur} EUR",
    ]
    if request.user_notes:
        parts.append(f"Anmerkungen: {request.user_notes}")
    parts.append(f"Discovery-Transkript:\n{request.transcript}")
    return "\n\n".join(parts)


def _render_few_shot(rv: RetrievedOffer) -> str:
    """Render one retrieved offer as a markdown reference block."""
    cj: dict[str, Any] = rv.latest_version.content_json
    if cj.get("format") == "legacy_markdown":
        body = cj.get("markdown", "")
    else:
        body = _content_to_markdown(cj)

    header = (
        f"### Referenz-Angebot — {rv.offer.client_name} "
        f"({rv.offer.consulting_type}, status={rv.offer.status}, "
        f"sim={rv.score:.2f})"
    )
    return f"{header}\n\n{body}"


def _content_to_markdown(content: dict[str, Any]) -> str:
    """Re-render structured content_json back to markdown for few-shot use."""
    lines: list[str] = []
    if title := content.get("angebot_titel"):
        lines.append(f"# {title}\n")
    if client := content.get("client_name"):
        lines.append(f"**Für:** {client}\n")
    if v := content.get("ausgangssituation"):
        lines.append(f"## Ausgangssituation\n\n{v}\n")
    if v := content.get("leistungsumfang_intro"):
        lines.append(f"## Leistungsumfang\n\n{v}\n")
    for i, b in enumerate(content.get("bestandteile") or [], start=1):
        lines.append(f"### Bestandteil {i} — {b.get('titel', '')}\n\n{b.get('beschreibung', '')}\n")
    if v := content.get("leistungserbringung"):
        lines.append(f"## Leistungserbringung\n\n{v}\n")
    if v := content.get("investition"):
        lines.append(f"## Investition\n\n{v}\n")
    if v := content.get("rahmenbedingungen"):
        lines.append(f"## Rahmenbedingungen\n\n{v}\n")
    return "\n".join(lines)


def _build_user_message(
    request: OfferGenerateRequest, retrieved: list[RetrievedOffer]
) -> str:
    """Assemble the user-turn message: few-shots + the actual generation task."""
    sections: list[str] = []
    if retrieved:
        sections.append(
            "## Referenz-Angebote (Stil und Struktur — nicht 1:1 kopieren)\n"
            + "\n\n---\n\n".join(_render_few_shot(rv) for rv in retrieved)
        )
    sections.append(
        "## Neues Angebot — Eingabedaten\n\n"
        f"- **Kunde:** {request.client_name}\n"
        f"- **Branche:** {request.industry or 'unbekannt'}\n"
        f"- **Beratungsart:** {request.consulting_type}\n"
        f"- **Investition (EUR, exkl. MwSt.):** {request.price_eur}\n"
        + (f"- **Anmerkungen vom Berater:** {request.user_notes}\n" if request.user_notes else "")
        + f"\n### Discovery-Call-Transkript\n\n{request.transcript}\n"
    )
    sections.append(
        "Erstelle jetzt das strukturierte Angebot über den `submit_offer`-Tool-Call."
    )
    return "\n\n".join(sections)


def _build_offer_tool() -> dict[str, Any]:
    """Anthropic tool spec derived from the Pydantic schema."""
    return {
        "name": "submit_offer",
        "description": (
            "Reicht das fertige Angebot als strukturiertes JSON-Objekt ein. "
            "Verwende dieses Tool als einzige Antwort."
        ),
        "input_schema": OfferContent.model_json_schema(),
    }


async def _call_claude_for_offer(
    system_blocks: list[dict[str, Any]],
    user_message: str,
) -> OfferContent:
    client = get_anthropic_client()
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system_blocks,
        tools=[_build_offer_tool()],
        tool_choice={"type": "tool", "name": "submit_offer"},
        messages=[{"role": "user", "content": user_message}],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Claude wurde vom Token-Limit abgeschnitten — Output ist unvollständig. "
            f"max_tokens={MAX_OUTPUT_TOKENS}, stop_reason={response.stop_reason}. "
            "Bitte den Transkript-Input prüfen oder MAX_OUTPUT_TOKENS erhöhen."
        )

    tool_blocks = [b for b in response.content if isinstance(b, ToolUseBlock)]
    if not tool_blocks:
        snippet = json.dumps([b.model_dump() for b in response.content])[:500]
        raise RuntimeError(f"Claude did not return a tool_use block: {snippet}")
    if tool_blocks[0].name != "submit_offer":
        raise RuntimeError(f"Unexpected tool: {tool_blocks[0].name}")

    return OfferContent.model_validate(tool_blocks[0].input)


async def generate_offer(
    request: OfferGenerateRequest,
    user_id: uuid.UUID | None,
    session: AsyncSession,
    k: int = DEFAULT_K,
) -> OfferGenerateResponse:
    """Run the full generation pipeline and persist the result."""
    query_text = _build_query_text(request)

    logger.info(
        f"[generate_offer] embedding query ({len(query_text)} chars) "
        f"for client={request.client_name!r}"
    )
    query_embedding = await embed_text(query_text, input_type="query")

    retrieved = await retrieve_similar_offers(session, query_embedding, k=k)
    logger.info(
        f"[generate_offer] retrieved {len(retrieved)} few-shots: "
        + ", ".join(f"{r.offer.client_name}={r.score:.2f}" for r in retrieved)
    )

    system_blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": SYSTEM_INSTRUCTIONS + "\n\n# Skelett-Referenz\n\n" + _load_skeleton(),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    user_message = _build_user_message(request, retrieved)

    content = await _call_claude_for_offer(system_blocks, user_message)

    offer = Offer(
        client_name=request.client_name,
        industry=request.industry,
        consulting_type=request.consulting_type,
        status="draft",
        price_eur=request.price_eur,
        user_id=user_id,
        co_consultant_id=request.co_consultant_id,
    )
    session.add(offer)
    await session.flush()

    version = OfferVersion(
        offer_id=offer.id,
        version_number=1,
        transcript=request.transcript,
        user_notes=request.user_notes,
        content_json=content.model_dump(mode="json"),
    )
    session.add(version)
    await session.flush()
    await session.commit()

    return OfferGenerateResponse(
        offer_id=offer.id,
        version_id=version.id,
        version_number=version.version_number,
        content=content,
        retrieved_offer_ids=[r.offer.id for r in retrieved],
        created_at=version.created_at or datetime.utcnow(),
    )
