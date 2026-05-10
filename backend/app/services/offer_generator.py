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
from app.services.knowledge import RetrievedKnowledge, render_knowledge_block, retrieve_knowledge
from app.services.llm import get_anthropic_client
from app.services.retrieval import RetrievedOffer, retrieve_similar_offers

settings = get_settings()

DEFAULT_K_FEW_SHOTS = 3
DEFAULT_K_KNOWLEDGE = 5
# 32768 lets Claude really fill out v2 (Saarpor-level depth: 5+ phases with
# 4 setup attributes each, 6+ leistungsumfang_items with full descriptions,
# 3 mehrwert layers with up to 6 bullets each, etc.). 16k still left the
# model summarizing prematurely on rich discoveries.
MAX_OUTPUT_TOKENS = 32768

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_SKELETON_PATH = _PROMPTS_DIR / "offer_skeleton.md"

SYSTEM_INSTRUCTIONS = """Du bist ein Senior-Berater der ERA Group und schreibst auf Deutsch verkaufsstarke, fachlich substantielle Angebote für KI-Strategie- und KI-Beratungs-Mandate.

ERZÄHL-ARCHITEKTUR
Ein gutes ERA-Angebot ist ein Verkaufspitch, kein Modul-Listing. Es führt durch:
1. Hook (Management Summary + zitierfähiger Insight + Markt-Argumentation)
2. Fundament (Ausgangssituation aus Discovery + erkannte Anwendungsfälle + Zielsetzung)
3. Vorgehen in 3–5 Phasen
4. Substanz (Technische Basis, dreistufiger Mehrwert, was konkret enthalten ist)
5. Investition + nächste Schritte

Du bekommst:
- ein Discovery-Call-Transkript (Pflicht)
- Domänen-Wissen aus dem KISB-Kompendium (Methodik, Reifegradmodell, 13-Schritte-Prozess, Change-Management — fachliche Grundlage, nicht zitieren)
- 0–3 Referenz-Angebote als Stil- und Struktur-Vorlage
- Mandat-Eingaben (Kunde, Branche, Beratungsart, Preis, optional Anmerkungen)

QUALITÄTSANSPRÜCHE
- Tiefe statt Breite. Schöpfe das Discovery-Transkript komplett aus — jeder relevante Pain-Point, jeder Stakeholder, jeder genannte Use-Case taucht im Angebot wieder auf. Wenn der Kunde fünf Anwendungsfelder erwähnt hat, sind fünf in `erkannte_anwendungsfaelle`. Nicht zwei.
- Konkret, nicht generisch. Statt "wir beraten Sie strategisch" → "Wir identifizieren mit Ihrem Führungskreis 2–3 priorisierte KI-Anwendungsfälle in Einkauf und Rechnungswesen, bewerten sie auf Aufwand-Nutzen und liefern eine Roadmap mit Quick-Wins zuerst."
- Storytelling, nicht Aufzählung. `management_summary` und `ausgangssituation` sind narrative Absätze (mind. 5 Sätze), keine Bullet-Listen. Bullets gibt es nur, wo das Schema sie verlangt.
- Fachliche Substanz aus dem Kompendium. Nutze die Methodik-Begriffe (Reifegrad, Anwendungsfall-Bewertung, Aufwand-Nutzen-Matrix, Roadmap, Mini-Business-Case, Triggerkarten, AI Design Sprint), wo sie zum Mandat passen — aber niemals als Buzzword-Salat.
- Sie-Form, professionell-direkt, kein Marketing-Fluff, kein Beraterdeutsch.

ANTI-PATTERNS (keinesfalls)
- Listen mit weniger als drei Punkten. Wenn nur zwei kommen würden: als Prosa formulieren.
- Generische Floskeln ("ganzheitlicher Ansatz", "wir sind Ihr Partner", "exzellente Ergebnisse").
- "Modul A, Modul B, …" als Phasenstruktur. Phasen haben sprechende Namen ("Vorbereitung", "Strategischer Workshop", "Vertiefung & Prototyp", "Umsetzung").
- Wiederholte Adjektive ("klar, klar, klar"). Variere oder weglassen.
- Preis ohne Wert-Argument. `investition` erklärt, was der Preis kauft.

SCHEMA-HINWEISE
- Antworte ausschließlich über den `submit_offer`-Tool-Call. Kein Text außerhalb.
- Felder direkt als Top-Level-Properties (kein `{"offer": {...}}`-Wrapper).
- Listen-Felder (`phasen`, `mehrwert_3_ebenen`, `leistungsumfang_items`, etc.) sind echte JSON-Arrays, niemals als String serialisiert.
- `mehrwert_3_ebenen` enthält EXAKT drei Ebenen, jede mit 3–5 Bullets.
- `phasen[*].beschreibung` mind. 80 Zeichen (≈ 2–3 Sätze), `phasen[*].ergebnis` benennt einen konkreten Output."""


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
    """Re-render structured content_json back to markdown for few-shot use.

    Handles both v1 (legacy 8-field) and v2 (storytelling) schemas so the
    Bestandsangebote-Pool keeps working as few-shot material.
    """
    lines: list[str] = []
    if title := content.get("angebot_titel"):
        lines.append(f"# {title}\n")
    if client := content.get("client_name"):
        lines.append(f"**Für:** {client}\n")

    # v2 (preferred) fields
    if v := content.get("management_summary"):
        lines.append(f"## Management Summary\n\n{v}\n")
    if v := content.get("hook_quote"):
        lines.append(f"> {v}\n")
    if warum := content.get("warum_jetzt_argumente"):
        lines.append("## Warum jetzt\n")
        for w in warum:
            lines.append(f"- {w}")
        lines.append("")
    if v := content.get("ausgangssituation"):
        lines.append(f"## Ausgangssituation\n\n{v}\n")
    if cases := content.get("erkannte_anwendungsfaelle"):
        lines.append("## Erkannte Anwendungsfälle\n")
        for c in cases:
            lines.append(f"- {c}")
        lines.append("")
    if v := content.get("zielsetzung_und_ergebnis"):
        lines.append(f"## Zielsetzung & Ergebnis\n\n{v}\n")
    if phasen := content.get("phasen"):
        lines.append("## Vorgehen\n")
        for p in phasen:
            line = f"### Phase {p.get('nummer','?')} — {p.get('titel','')}"
            if p.get("untertitel"):
                line += f" ({p['untertitel']})"
            lines.append(line + "\n")
            if p.get("beschreibung"):
                lines.append(f"{p['beschreibung']}\n")
            meta = ", ".join(
                f"{k}: {p[k]}"
                for k in ("dauer", "format", "teilnehmer", "moderation")
                if p.get(k)
            )
            if meta:
                lines.append(f"_{meta}_\n")
            for a in (p.get("aktivitaeten") or []):
                lines.append(f"- {a}")
            if p.get("ergebnis"):
                lines.append(f"\n**Ergebnis:** {p['ergebnis']}\n")
    if tech := content.get("technische_basis"):
        lines.append("## Technische Basis\n")
        for t in tech:
            lines.append(f"### {t.get('titel','')}\n\n{t.get('beschreibung','')}\n")
    if mehrwert := content.get("mehrwert_3_ebenen"):
        lines.append("## Mehrwert auf drei Ebenen\n")
        for m in mehrwert:
            lines.append(f"### {m.get('ebene','')}")
            for p in (m.get("punkte") or []):
                lines.append(f"- {p}")
            lines.append("")
    if items := content.get("leistungsumfang_items"):
        lines.append("## Leistungsumfang\n")
        for it in items:
            lines.append(
                f"{it.get('nummer','?')}. **{it.get('titel','')}** — {it.get('beschreibung','')}"
            )
        lines.append("")
    if v := content.get("investition"):
        lines.append(f"## Investition\n\n{v}\n")
    if v := content.get("naechste_schritte"):
        lines.append(f"## Nächste Schritte\n\n{v}\n")

    # v1 fallthrough (legacy)
    if v := content.get("leistungsumfang_intro"):
        lines.append(f"## Leistungsumfang (v1)\n\n{v}\n")
    for i, b in enumerate(content.get("bestandteile") or [], start=1):
        lines.append(f"### Bestandteil {i} — {b.get('titel', '')}\n\n{b.get('beschreibung', '')}\n")
    if v := content.get("leistungserbringung"):
        lines.append(f"## Leistungserbringung (v1)\n\n{v}\n")
    if v := content.get("rahmenbedingungen"):
        lines.append(f"## Rahmenbedingungen (v1)\n\n{v}\n")
    return "\n".join(lines)


def _build_user_message(
    request: OfferGenerateRequest,
    retrieved: list[RetrievedOffer],
    knowledge: list[RetrievedKnowledge],
) -> str:
    """Assemble the user-turn message: knowledge + few-shots + the actual generation task."""
    sections: list[str] = []

    # Knowledge first — provides domain-substance context Claude reasons over
    # before it sees the discovery + reference-offers.
    knowledge_block = render_knowledge_block(knowledge)
    if knowledge_block:
        sections.append(knowledge_block)

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
    # The Anthropic SDK requires streaming for any request whose worst-case
    # latency exceeds 10 minutes (i.e. effectively whenever max_tokens is
    # large). Use the streaming API and pull the final assembled message at
    # the end — semantics-equivalent to the previous create() call.
    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system_blocks,
        tools=[_build_offer_tool()],
        tool_choice={"type": "tool", "name": "submit_offer"},
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = await stream.get_final_message()

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

    return OfferContent.model_validate(_unwrap_tool_input(tool_blocks[0].input))


def _unwrap_tool_input(tool_input: Any) -> Any:
    """Tolerate a single-key wrapper like `{"offer": {...}}` around the payload.

    Claude Opus 4.7 occasionally wraps the structured tool input even when the
    schema is flat, which makes Pydantic fail with all fields missing. If we
    spot a single top-level key whose value already matches OfferContent, we
    unwrap once and log it.
    """
    if not isinstance(tool_input, dict):
        return tool_input
    expected = set(OfferContent.model_fields.keys())
    if expected & tool_input.keys():
        return tool_input
    if len(tool_input) == 1:
        wrapper_key, inner = next(iter(tool_input.items()))
        if isinstance(inner, dict) and (expected & inner.keys()):
            logger.warning(
                f"[generate_offer] Claude wrapped offer under {wrapper_key!r}; unwrapping."
            )
            return inner
    return tool_input


async def generate_offer(
    request: OfferGenerateRequest,
    user_id: uuid.UUID | None,
    session: AsyncSession,
    k_few_shots: int = DEFAULT_K_FEW_SHOTS,
    k_knowledge: int = DEFAULT_K_KNOWLEDGE,
) -> OfferGenerateResponse:
    """Run the full generation pipeline and persist the result."""
    query_text = _build_query_text(request)

    logger.info(
        f"[generate_offer] embedding query ({len(query_text)} chars) "
        f"for client={request.client_name!r}"
    )
    query_embedding = await embed_text(query_text, input_type="query")

    retrieved = await retrieve_similar_offers(session, query_embedding, k=k_few_shots)
    logger.info(
        f"[generate_offer] retrieved {len(retrieved)} few-shots: "
        + ", ".join(f"{r.offer.client_name}={r.score:.2f}" for r in retrieved)
    )

    knowledge = await retrieve_knowledge(session, query_embedding, k=k_knowledge)
    logger.info(
        f"[generate_offer] retrieved {len(knowledge)} knowledge chunks: "
        + ", ".join(
            f"{(r.chunk.chapter or '?')}/{(r.chunk.title or '')[:30]}={r.score:.2f}"
            for r in knowledge
        )
    )

    system_blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": SYSTEM_INSTRUCTIONS + "\n\n# Skelett-Referenz\n\n" + _load_skeleton(),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    user_message = _build_user_message(request, retrieved, knowledge)

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
        knowledge_chunk_count=len(knowledge),
        created_at=version.created_at or datetime.utcnow(),
    )
