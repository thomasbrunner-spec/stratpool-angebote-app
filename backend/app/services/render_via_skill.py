"""Render an offer to .pptx via the Anthropic skills + code-execution pipeline.

Replaces the python-pptx-in-Backend approach. Claude:
  1. loads our custom era-presentation skill (CI rules + template)
  2. loads the built-in `pptx` skill (python-pptx environment)
  3. is shown the few-shot reference decks via container_upload blocks
  4. composes a deck with python-pptx in the sandbox
  5. writes a .pptx file we then download via the Files API
"""

from __future__ import annotations

import time
from decimal import Decimal

import anthropic
from loguru import logger

from app.config import get_settings
from app.models.consultant import Consultant

settings = get_settings()

_BETAS = ["skills-2025-10-02", "code-execution-2025-05-22", "files-api-2025-04-14"]
_MAX_TOKENS = 16384


class RenderError(RuntimeError):
    pass


def _build_user_message(
    *,
    transcript: str,
    user_notes: str | None,
    client_name: str,
    industry: str | None,
    consulting_type: str,
    price_eur: Decimal | None,
    co_consultant: Consultant | None,
    few_shot_file_ids: list[str],
) -> list[dict]:
    """Compose the multipart user message for the rendering request."""
    parts: list[dict] = []

    # 1. The reference decks — Claude sees them as containers it can open.
    for fid in few_shot_file_ids:
        parts.append({"type": "container_upload", "file_id": fid})

    # 2. The textual brief.
    co_block = ""
    if co_consultant is not None:
        co_block = (
            f"\n## Co-Berater (Layout-Block links unten)\n"
            f"- Name: {co_consultant.name}\n"
            f"- Titel: {co_consultant.titel or '(nicht angegeben)'}\n"
            f"- Tel: {co_consultant.tel or '(nicht angegeben)'}\n"
            f"- E-Mail: {co_consultant.email or '(nicht angegeben)'}\n"
        )

    price_line = f"- Investition (EUR, exkl. MwSt.): {price_eur}\n" if price_eur else ""
    notes_line = f"- Anmerkungen vom Berater: {user_notes}\n" if user_notes else ""

    text = f"""Erstelle eine ERA-Group-Projektskizze als .pptx für das folgende Mandat. Nutze den era-presentation Skill für die ERA-CI und die hochgeladenen Referenz-Decks als stilistische Vorlage (Folien-Anzahl, Layout-Mix, Tonfall).

## Hauptberater (Overlay-Box rechts unten — siehe Skill-Sektion "Zwei Berater auf der Titelfolie")
- Name: {settings.berater_name}
- Titel: {settings.berater_titel}
- Tel: {settings.berater_tel}
- E-Mail: {settings.berater_email}
{co_block}
## Mandat
- Kunde: {client_name}
- Branche: {industry or 'unbekannt'}
- Beratungsart: {consulting_type}
{price_line}{notes_line}
## Discovery-Transkript

{transcript}

## Anweisungen
- Folge der ERA-CI strikt (Trebuchet MS, Farben, Footer/Logo aus Master).
- Cover-Folie mit beiden Beratern wie im Skill beschrieben.
- Nutze die hochgeladenen Referenz-Decks als Vorlage für Stil und Folien-Aufbau, NICHT 1:1 kopieren — Inhalt muss zum vorliegenden Mandat passen.
- Body-Text in Content-Folien standardmäßig regular (nicht fett).
- Schreibe das Deck nach `/home/claude/angebot.pptx` und führe die QA-Schritte aus dem Skill aus.
- Antworte am Ende mit dem absoluten Pfad zum fertigen .pptx und einer 1-Satz-Zusammenfassung."""

    # Mark the text block as the cache breakpoint. Anthropic caches everything
    # *up to* this block — i.e. every container_upload (the few-shot decks)
    # gets cached. Subsequent renders within ~5 minutes pay ~10% of the input
    # cost for the cached portion, which makes few-shots affordable.
    parts.append(
        {
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }
    )
    return parts


def _extract_pptx_file_id(response) -> str | None:
    """Walk every tool result, return the first file_id whose downloaded bytes are a zip."""
    return None  # actual download happens in render_offer_via_skill below


async def render_offer_via_skill(
    *,
    transcript: str,
    user_notes: str | None,
    client_name: str,
    industry: str | None,
    consulting_type: str,
    price_eur: Decimal | None,
    co_consultant: Consultant | None,
) -> bytes:
    """Trigger Claude to compose and render the offer; return the pptx bytes."""
    if not settings.era_presentation_skill_id:
        raise RenderError("ERA_PRESENTATION_SKILL_ID is not configured")
    # Few-shot decks are optional. They make outputs more on-style, but each
    # one balloons the input by hundreds of thousands of tokens — keep them
    # off until prompt-caching is wired up.
    few_shots = settings.few_shot_file_id_list

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_content = _build_user_message(
        transcript=transcript,
        user_notes=user_notes,
        client_name=client_name,
        industry=industry,
        consulting_type=consulting_type,
        price_eur=price_eur,
        co_consultant=co_consultant,
        few_shot_file_ids=few_shots,
    )

    t0 = time.time()
    logger.info(
        f"[render_via_skill] starting render for client={client_name!r} "
        f"few_shots={len(few_shots)} co_consultant={co_consultant is not None}"
    )

    # Snapshot existing file_ids so we can spot new ones the model creates.
    # Anthropic's tool-result block walking is brittle (the file id surface
    # depends on which sub-tool — bash / text_editor / code_execution — wrote
    # the file), so we use the Files API as a robust fallback.
    pre_files = {f.id for f in (await client.beta.files.list(limit=100, betas=["files-api-2025-04-14"])).data}

    response = await client.beta.messages.create(
        model=settings.render_model,
        max_tokens=_MAX_TOKENS,
        container={
            "skills": [
                {"skill_id": "pptx", "type": "anthropic", "version": "latest"},
                {
                    "skill_id": settings.era_presentation_skill_id,
                    "type": "custom",
                    "version": "latest",
                },
            ],
        },
        tools=[{"type": "code_execution_20260120", "name": "code_execution"}],
        messages=[{"role": "user", "content": user_content}],
        betas=_BETAS,
    )
    logger.info(
        f"[render_via_skill] response in {time.time() - t0:.1f}s — "
        f"stop_reason={response.stop_reason} "
        f"tokens=in:{response.usage.input_tokens}/out:{response.usage.output_tokens}"
    )

    # Pick the .pptx via the Files-API delta. Robust across all sub-tool variants
    # (bash / text_editor / code_execution) — we just look for new zip files.
    post = (
        await client.beta.files.list(limit=100, betas=["files-api-2025-04-14"])
    ).data
    new_files = [f for f in post if f.id not in pre_files]
    # Newest first, prefer .pptx then any zip
    new_files.sort(key=lambda f: f.created_at, reverse=True)
    for f in new_files:
        if not (f.filename or "").lower().endswith(".pptx") and "zip" not in (f.mime_type or ""):
            continue
        response_obj = await client.beta.files.download(
            f.id, betas=["files-api-2025-04-14"]
        )
        data = await response_obj.read()
        if data[:2] != b"PK":
            continue
        logger.info(
            f"[render_via_skill] picked {f.filename!r} ({f.id}, {len(data):,} B)"
        )
        return data

    raise RenderError(
        f"No .pptx file was produced. stop_reason={response.stop_reason} "
        f"new_files={len(new_files)}"
    )
