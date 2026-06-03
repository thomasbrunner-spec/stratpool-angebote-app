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
# 32k is needed once the deck grows to the storytelling architecture
# (Cover + Mgmt Summary + Hook + Markt + Ausgangslage + Zielsetzung +
#  Phasen-Übersicht + 4 Phase-Detail-Slides + Tech + Mehrwert + Items
#  + Investition + CTA + Bio = 14–17 slides, each composed via the
#  python-pptx recipes from SKILL.md). With 16k Claude was hitting
#  max_tokens before saving the file (stop_reason=max_tokens, no .pptx).
_MAX_TOKENS = 32768

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
    offer_content_json: dict | None = None,
) -> list[dict]:
    """Compose the multipart user message for the rendering request.

    `offer_content_json` is the storytelling-schema payload the user has
    finalised in the editor. It's the single source of truth for the slide
    content (slides 2..N+5 in the SKILL recipe). The discovery transcript
    is kept as background context for details that don't fit the schema.
    """
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

    content_block = ""
    if offer_content_json:
        # Pretty-print so it's clearly a contract, not raw JSON noise.
        import json as _json
        pretty = _json.dumps(offer_content_json, ensure_ascii=False, indent=2)
        content_block = (
            "\n## Freigegebenes Angebot (führend für die Inhalte der Folien 2..N)\n\n"
            "Das folgende JSON ist die vom Berater finalisierte Inhaltsversion. "
            "Du nutzt diese Felder 1:1 für die jeweils im Skill beschriebenen "
            "Slides (siehe Recipes-Tabelle: management_summary → Slide 2, "
            "hook_quote → Slide 3, warum_jetzt_argumente → Slide 4, "
            "ausgangssituation + erkannte_anwendungsfaelle → Slide 5, "
            "zielsetzung_und_ergebnis → Slide 6, phasen → Übersicht + je eine "
            "Detail-Slide, technische_basis → Tech-Slide, mehrwert_3_ebenen → "
            "Mehrwert-Slide, leistungsumfang_items → Leistungs-Slide, "
            "investition → Hero-Slide, naechste_schritte → CTA-Slide).\n\n"
            "Erfinde KEINE Inhalte, die nicht im JSON oder im Discovery stehen. "
            "Erkenne fehlende oder zu kurze Felder und gleiche sie mit Material "
            "aus dem Discovery-Transkript aus, niemals mit generischen Floskeln.\n\n"
            f"```json\n{pretty}\n```\n"
        )

    text = f"""Erstelle ein {spec.pptx_or_docx_label} für das folgende ERA-Group-Beratungsmandat. Nutze den {skill_name}-Skill für die ERA-CI **und folge der dort beschriebenen Standard-Architektur (Cover → Management Summary → Hook → Warum jetzt → Ausgangssituation → Zielsetzung → Phasen-Übersicht → Phase-Detail-Slides → Tech → Mehrwert → Leistungsumfang → Investition → CTA → Ansprechpartner). Default-Layout für Body-Slides ist `Leer` mit eigenen Kompositionen, NICHT `1 x Content`.**

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
{price_line}{notes_line}{content_block}
## Discovery-Transkript (Hintergrund-Kontext, sekundär)

{transcript}

## Anweisungen
- Folge der ERA-CI strikt (Schriften, Farben, Logo, Header/Footer wo vorgesehen) und der Standard-Architektur aus dem Skill.
- Inhalt aus dem freigegebenen Angebot-JSON ist führend; das Transkript dient nur zur Kontext-Anreicherung.
- Body-Text in normaler Schrift (regular), nicht fett (außer für Headlines/Hervorhebungen).
- Body-Folien nutzen mehrheitlich `Leer`-Layout mit eigenen Kompositionen (siehe SKILL Recipes). KEIN durchgehender Einsatz von `1 x Content`.
- KEINE Bullet-Listen mit weniger als 3 Punkten. KEIN „Modul A/B/C"-Pattern.
- Schreibe das Ergebnis nach `$OUTPUT_DIR/{spec.output_filename}` (workspace output dir, damit die Datei vom Host abgeholt werden kann — nicht nach `/home/claude/`, die Bytes erreichen den Host sonst nicht) und führe die im Skill beschriebenen QA-Schritte aus.
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
    offer_content_json: dict | None = None,
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
        offer_content_json=offer_content_json,
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

    # Streaming mandatory at this token count — see offer_generator for the
    # same pattern. The Anthropic SDK rejects non-streamed long requests.
    async with client.beta.messages.stream(
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
    ) as stream:
        response = await stream.get_final_message()
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
