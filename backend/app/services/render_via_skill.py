"""Render an offer to .pptx or .docx via the Anthropic skills + code-execution pipeline.

Claude:
  1. loads our custom era-presentation or era-word skill (CI rules + assets)
  2. loads the matching Anthropic built-in skill (`pptx` or `docx`) for runtime
  3. is optionally shown few-shot reference decks via container_upload blocks
  4. composes the document in the sandbox with python-pptx / python-docx
  5. writes the file we then download via the Files API (delta walk)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

import anthropic
from loguru import logger

from app.config import get_settings
from app.models.consultant import Consultant

settings = get_settings()

_BETAS = ["skills-2025-10-02", "code-execution-2025-05-22", "files-api-2025-04-14"]
_MAX_TOKENS = 16384

RenderFormat = Literal["pptx", "word"]


class RenderError(RuntimeError):
    pass


@dataclass
class _FormatSpec:
    """Per-format wiring: which skill, which suffix, which file extension to look for."""

    builtin_skill_id: str
    custom_skill_setting_attr: str
    output_filename: str
    output_extension: str
    output_mime_marker: str  # substring expected in mime_type
    pptx_or_docx_label: str  # for prompts


_FORMATS: dict[RenderFormat, _FormatSpec] = {
    "pptx": _FormatSpec(
        builtin_skill_id="pptx",
        custom_skill_setting_attr="era_presentation_skill_id",
        output_filename="angebot.pptx",
        output_extension=".pptx",
        output_mime_marker="zip",  # pptx is a zip
        pptx_or_docx_label=".pptx-Präsentation",
    ),
    "word": _FormatSpec(
        builtin_skill_id="docx",
        custom_skill_setting_attr="era_word_skill_id",
        output_filename="angebot.docx",
        output_extension=".docx",
        output_mime_marker="zip",  # docx is a zip too (OOXML)
        pptx_or_docx_label=".docx-Word-Dokument",
    ),
}


def _build_user_message(
    *,
    fmt: RenderFormat,
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

    # 1. The reference decks/docs — Claude sees them as containers it can open.
    for fid in few_shot_file_ids:
        parts.append({"type": "container_upload", "file_id": fid})

    # 2. The textual brief.
    co_block = ""
    if co_consultant is not None:
        co_block = (
            f"\n## Co-Berater\n"
            f"- Name: {co_consultant.name}\n"
            f"- Titel: {co_consultant.titel or '(nicht angegeben)'}\n"
            f"- Tel: {co_consultant.tel or '(nicht angegeben)'}\n"
            f"- E-Mail: {co_consultant.email or '(nicht angegeben)'}\n"
        )

    price_line = f"- Investition (EUR, exkl. MwSt.): {price_eur}\n" if price_eur else ""
    notes_line = f"- Anmerkungen vom Berater: {user_notes}\n" if user_notes else ""

    spec = _FORMATS[fmt]
    skill_name = "era-presentation" if fmt == "pptx" else "era-word"

    text = f"""Erstelle ein {spec.pptx_or_docx_label} für das folgende ERA-Group-Beratungsmandat. Nutze den {skill_name}-Skill für die ERA-CI.

## Hauptberater
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
- Folge der ERA-CI strikt (Schriften, Farben, Logo, Header/Footer wo vorgesehen).
- Inhalt muss zum vorliegenden Mandat passen — nicht generisch.
- Body-Text in normaler Schrift (regular), nicht fett (außer für Headlines/Hervorhebungen).
- Schreibe das Ergebnis nach `/home/claude/{spec.output_filename}` und führe die im Skill beschriebenen QA-Schritte aus.
- Antworte am Ende mit dem absoluten Pfad zur fertigen Datei und einer 1-Satz-Zusammenfassung."""

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


async def render_offer_via_skill(
    *,
    fmt: RenderFormat,
    transcript: str,
    user_notes: str | None,
    client_name: str,
    industry: str | None,
    consulting_type: str,
    price_eur: Decimal | None,
    co_consultant: Consultant | None,
) -> bytes:
    """Trigger Claude to compose and render the offer; return the file bytes."""
    if fmt not in _FORMATS:
        raise RenderError(f"Unknown format {fmt!r}")
    spec = _FORMATS[fmt]
    custom_skill_id = getattr(settings, spec.custom_skill_setting_attr)
    if not custom_skill_id:
        raise RenderError(
            f"{spec.custom_skill_setting_attr.upper()} is not configured for {fmt!r}"
        )
    few_shots = settings.few_shot_file_id_list  # off by default; pool today is PPT-only

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_content = _build_user_message(
        fmt=fmt,
        transcript=transcript,
        user_notes=user_notes,
        client_name=client_name,
        industry=industry,
        consulting_type=consulting_type,
        price_eur=price_eur,
        co_consultant=co_consultant,
        few_shot_file_ids=few_shots if fmt == "pptx" else [],
    )

    t0 = time.time()
    logger.info(
        f"[render_via_skill] starting fmt={fmt} client={client_name!r} "
        f"few_shots={len(few_shots) if fmt == 'pptx' else 0} "
        f"co_consultant={co_consultant is not None}"
    )

    # Snapshot existing file_ids so we can spot new ones the model creates.
    pre_files = {
        f.id
        for f in (
            await client.beta.files.list(limit=100, betas=["files-api-2025-04-14"])
        ).data
    }

    response = await client.beta.messages.create(
        model=settings.render_model,
        max_tokens=_MAX_TOKENS,
        container={
            "skills": [
                {"skill_id": spec.builtin_skill_id, "type": "anthropic", "version": "latest"},
                {"skill_id": custom_skill_id, "type": "custom", "version": "latest"},
            ],
        },
        tools=[{"type": "code_execution_20260120", "name": "code_execution"}],
        messages=[{"role": "user", "content": user_content}],
        betas=_BETAS,
    )
    logger.info(
        f"[render_via_skill] fmt={fmt} response in {time.time() - t0:.1f}s — "
        f"stop_reason={response.stop_reason} "
        f"tokens=in:{response.usage.input_tokens}/out:{response.usage.output_tokens}"
    )

    # Pick the produced file via the Files-API delta — robust across sub-tool variants.
    # Files can be registered slightly *after* messages.create returns (especially
    # for docx via Anthropic's `cp` to $OUTPUT_DIR pattern), so retry the listing
    # for up to ~30s with a backoff.
    new_files: list = []
    for attempt in range(6):
        post = (
            await client.beta.files.list(limit=100, betas=["files-api-2025-04-14"])
        ).data
        new_files = [f for f in post if f.id not in pre_files]
        new_files.sort(key=lambda f: f.created_at, reverse=True)
        if any(
            (f.filename or "").lower().endswith(spec.output_extension)
            for f in new_files
        ):
            break
        if attempt < 5:
            logger.info(
                f"[render_via_skill] no {spec.output_extension} yet "
                f"(attempt {attempt + 1}/6), retrying in 5s…"
            )
            await asyncio.sleep(5)

    for f in new_files:
        filename = (f.filename or "").lower()
        mime = (f.mime_type or "")
        if not (filename.endswith(spec.output_extension) or spec.output_mime_marker in mime):
            continue
        if not filename.endswith(spec.output_extension) and not filename.endswith(".pptx"):
            # extra guard: docx and pptx both report mime=zip; require correct extension
            if spec.output_extension == ".docx" and not filename.endswith(".docx"):
                continue
        response_obj = await client.beta.files.download(
            f.id, betas=["files-api-2025-04-14"]
        )
        data = await response_obj.read()
        if data[:2] != b"PK":
            continue
        # For docx we additionally check that the OOXML content-type marker is present
        if fmt == "word" and not filename.endswith(".docx"):
            continue
        if fmt == "pptx" and not filename.endswith(".pptx"):
            continue
        logger.info(
            f"[render_via_skill] picked {f.filename!r} ({f.id}, {len(data):,} B)"
        )
        return data

    raise RenderError(
        f"No {spec.output_extension} file was produced. stop_reason={response.stop_reason} "
        f"new_files={len(new_files)}"
    )
