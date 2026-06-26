"""Pydantic schemas for the offer generation pipeline.

The `OfferContent` schema is the single source of truth for the structured
JSON Claude returns and that gets persisted in `offer_versions.content_json`.
The same schema drives the Anthropic tool-use spec — keep them in sync.

Schema lineage
--------------
v1 (legacy, no longer produced) had eight flat fields:
    angebot_titel, client_name, ausgangssituation, leistungsumfang_intro,
    bestandteile, leistungserbringung, investition, rahmenbedingungen.

v2 (current) follows the storytelling architecture observed in the
ERA-Group Saarpor reference deck: hook, market argument, situation,
hypotheses, target, phases, tech basis, three-level value, listed
deliverables, investment, CTA. The Storytelling structure is what
turns a "list of modules" into a "presentation that closes a deal".

Old offers in the DB stay as-is in `offer_versions.content_json`; the
list/detail filter ignores them via the version-presence of the new
`phasen` key. Re-rendering an old offer requires re-generating it.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from annotated_types import MaxLen
from json_repair import repair_json
from loguru import logger
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.models.offer import CONSULTING_TYPES

ConsultingType = Literal["ki_strategie", "ai_design_sprint", "prozessberatung", "workshop"]
OfferStatus = Literal["draft", "sent", "won", "lost"]
# Sanity: keep the literal in lockstep with the ORM constraint values.
assert set(CONSULTING_TYPES) == set(ConsultingType.__args__)  # type: ignore[attr-defined]


class OfferGenerateRequest(BaseModel):
    """Input for POST /api/v1/offers/generate."""

    client_name: str = Field(min_length=1, max_length=200)
    consulting_type: ConsultingType
    industry: str | None = Field(default=None, max_length=200)
    price_eur: Decimal = Field(gt=0)
    transcript: str = Field(min_length=50, description="Discovery-call transcript")
    user_notes: str | None = Field(default=None, max_length=5000)
    co_consultant_id: uuid.UUID | None = Field(
        default=None,
        description="Optional consultant from the consultants table — appears as second person on the cover slide",
    )


# ---------------- defensive-coercion helpers ----------------

# Top-level fields whose items are plain strings (not nested objects). Used to
# decide where dict-shaped list items get flattened back into text.
_STRING_LIST_FIELDS = {"warum_jetzt_argumente", "erkannte_anwendungsfaelle"}


def _try_parse_json_list(v: str) -> Any:
    """Recover a list from a JSON-string-encoded array (Opus tool-use quirk).

    Three flavours observed in production:
      1. Clean JSON array string — `json.loads` handles it directly.
      2. Pseudo-JSON with literal `\\n`/`\\t` — unescape and retry.
      3. Broken JSON (stray quotes, trailing commas) — `json-repair`.

    Returns the original string unchanged if none of the strategies yield a
    list, so the caller can let Pydantic raise a clean type error.
    """
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        pass
    try:
        unescaped = v.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
        return json.loads(unescaped)
    except json.JSONDecodeError:
        pass
    try:
        repaired = repair_json(v, return_objects=True)
        if isinstance(repaired, list):
            logger.warning(
                f"[schema] _try_parse_json_list: recovered via json-repair "
                f"(len={len(v)}, first 120={v[:120]!r})"
            )
            return repaired
    except Exception as exc:  # noqa: BLE001 — json-repair is best-effort
        logger.warning(f"[schema] json-repair also failed: {exc}")
    return v


def _coerce_to_text(item: Any) -> Any:
    """Flatten a dict-shaped bullet back into a string.

    Opus tool-use sometimes emits a string-list item as a small dict
    (e.g. ``{"Vermeidung des 95%-Effekts": ""}`` or
    ``{"ebene": "Menschlich", "punkt": "... statt Top-Down-Rollout"}``).
    We join the non-empty string values, falling back to the keys, so the
    content survives instead of failing the whole generation. Non-dict,
    non-string items pass through for Pydantic to reject cleanly.
    """
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        values = [v.strip() for v in item.values() if isinstance(v, str) and v.strip()]
        if values:
            return " — ".join(values)
        keys = [str(k).strip() for k in item if str(k).strip()]
        if keys:
            return " — ".join(keys)
    return item


def _max_len(field: Any) -> int | None:
    """Read the declared ``max_length`` cap off a Pydantic FieldInfo, if any."""
    for meta in field.metadata:
        if isinstance(meta, MaxLen):
            return meta.max_length
    return None


# ---------------- v2 sub-models ----------------


class OfferPhase(BaseModel):
    """One phase of the proposed engagement (typically 3–5 phases per offer)."""

    nummer: int = Field(ge=1, le=8, description="1-indexed phase number")
    titel: str = Field(min_length=1, max_length=120)
    untertitel: str | None = Field(default=None, max_length=200, description="Short subline for the phase header")
    beschreibung: str = Field(
        min_length=80,
        description="Two-to-four sentences narrating the phase's purpose and approach.",
    )
    dauer: str | None = Field(
        default=None,
        max_length=120,
        description='Free-form duration string ("ein Tag", "2 Wochen").',
    )
    format: str | None = Field(
        default=None,
        max_length=120,
        description='Setting (e.g. "vor Ort", "remote", "hybrid", "Workshop mit 6–8 Personen").',
    )
    teilnehmer: str | None = Field(default=None, max_length=200)
    moderation: str | None = Field(default=None, max_length=200)
    aktivitaeten: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="Key activities, 3-6 short bullets. Stays empty when the prose covers it.",
    )
    ergebnis: str = Field(
        min_length=20,
        description="What concretely comes out of this phase (deliverable, decision, artifact).",
    )


class OfferTechOption(BaseModel):
    """One technical-basis option (e.g. local / EU cloud / hybrid)."""

    titel: str = Field(min_length=1, max_length=80)
    beschreibung: str = Field(min_length=20, max_length=500)


class OfferMehrwertEbene(BaseModel):
    """One value layer (strategic / organizational / human)."""

    ebene: str = Field(min_length=1, max_length=40, description='e.g. "Strategisch"')
    punkte: list[str] = Field(
        min_length=3,
        max_length=6,
        description="3-6 substantive bullet points per layer — never fewer than 3.",
    )

    @field_validator("punkte", mode="before")
    @classmethod
    def _normalize_punkte(cls, v: Any) -> Any:
        """Tolerate JSON-string encoding, dict-shaped items and over-long lists.

        Opus tool-use occasionally emits the bullets of a value layer as dicts
        instead of strings (see _coerce_to_text) and overshoots the 6-item cap.
        Coerce + truncate rather than fail the whole offer over a formatting
        quirk. Too-few bullets still raises — we never fabricate content.
        """
        if isinstance(v, str):
            v = _try_parse_json_list(v)
        if isinstance(v, list):
            v = [_coerce_to_text(x) for x in v]
            cap = _max_len(cls.model_fields["punkte"])
            if cap is not None and len(v) > cap:
                logger.warning(f"[schema] truncating mehrwert punkte {len(v)} -> {cap}")
                v = v[:cap]
        return v


class OfferLeistungsItem(BaseModel):
    """One numbered deliverable line on the 'what's included' slide."""

    nummer: int = Field(ge=1)
    titel: str = Field(min_length=1, max_length=120)
    beschreibung: str = Field(min_length=20, max_length=400)


# ---------------- v2 root ----------------


class OfferContent(BaseModel):
    """Structured offer payload (v2), one row per OfferVersion.content_json."""

    angebot_titel: str = Field(min_length=1, max_length=200)
    client_name: str = Field(min_length=1, max_length=200)

    # Hero / hook block
    management_summary: str = Field(
        min_length=300,
        description=(
            "One paragraph (≈ 5–10 sentences) that frames the situation, the "
            "intervention, and the outcome. The cover-narrative of the deck."
        ),
    )
    hook_quote: str = Field(
        min_length=40,
        max_length=400,
        description=(
            'A single, quote-able insight (e.g. "Der Schlüssel liegt nicht in '
            'der Technologie — sondern in der Fähigkeit …"). Used as a '
            "stand-alone slide."
        ),
    )
    warum_jetzt_argumente: list[str] = Field(
        min_length=2,
        max_length=5,
        description="2–5 short market / urgency arguments — one per bullet, each a complete thought.",
    )

    # Discovery-grounded body
    ausgangssituation: str = Field(
        min_length=200,
        description="Customer's current state, derived from the transcript. Concrete, not generic.",
    )
    erkannte_anwendungsfaelle: list[str] = Field(
        min_length=3,
        max_length=10,
        description="Concrete AI / consulting use-cases extractable from the transcript.",
    )
    zielsetzung_und_ergebnis: str = Field(
        min_length=200,
        description="Goal of the engagement and the expected outcome — what the customer ends up with.",
    )

    # Phases (replaces v1 'bestandteile')
    phasen: list[OfferPhase] = Field(
        min_length=2,
        max_length=6,
        description="2–6 sequential phases. Each phase becomes its own deck slide.",
    )

    # Supporting blocks
    technische_basis: list[OfferTechOption] = Field(
        min_length=2,
        max_length=4,
        description="Tech setup options (e.g. local / EU cloud / hybrid). 2–4 items.",
    )
    mehrwert_3_ebenen: list[OfferMehrwertEbene] = Field(
        min_length=3,
        max_length=3,
        description="Exactly three layers: typically Strategisch / Organisatorisch / Menschlich.",
    )
    leistungsumfang_items: list[OfferLeistungsItem] = Field(
        min_length=4,
        max_length=12,
        description="Numbered list of what is concretely delivered. Substantive, not summary.",
    )

    investition: str = Field(
        min_length=100,
        description=(
            "Investment block: price + value rationale + scope notes. "
            "Do NOT just repeat the price — explain what it buys."
        ),
    )
    naechste_schritte: str = Field(
        min_length=80,
        description="Concrete next steps and a soft call-to-action.",
    )

    # ---- defensive validators (Claude Opus 4.7 quirks) ----

    @field_validator(
        "warum_jetzt_argumente",
        "erkannte_anwendungsfaelle",
        "phasen",
        "technische_basis",
        "mehrwert_3_ebenen",
        "leistungsumfang_items",
        mode="before",
    )
    @classmethod
    def _normalize_list_field(cls, v: Any, info: ValidationInfo) -> Any:
        """Repair three Opus tool-use quirks before Pydantic validates a list.

        1. The whole array arrives JSON-string-encoded (see _try_parse_json_list).
        2. A string-list item arrives as a dict (see _coerce_to_text); only
           applied to the plain-string fields, never to nested-object lists.
        3. The model overshoots the declared cap (e.g. 6 'warum_jetzt' instead
           of 5). Truncating to the cap keeps the best content and the deck
           layout contract, instead of throwing away the whole generation.

        We only ever drop excess items — too-few still raises, so we never
        fabricate content the consultant didn't get.
        """
        if isinstance(v, str):
            v = _try_parse_json_list(v)
        if not isinstance(v, list):
            return v
        if info.field_name in _STRING_LIST_FIELDS:
            v = [_coerce_to_text(x) for x in v]
        cap = _max_len(cls.model_fields[info.field_name])
        if cap is not None and len(v) > cap:
            logger.warning(
                f"[schema] truncating {info.field_name} {len(v)} -> {cap} (Opus overshoot)"
            )
            v = v[:cap]
        return v


# ---------------- API responses ----------------


class OfferGenerateResponse(BaseModel):
    """Response returned by POST /api/v1/offers/generate."""

    offer_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    content: OfferContent
    retrieved_offer_ids: list[uuid.UUID] = Field(
        description="IDs of the Bestandsangebote used as few-shots, ordered by similarity"
    )
    knowledge_chunk_count: int = Field(
        default=0,
        description="How many domain-knowledge chunks were merged into the prompt",
    )
    created_at: datetime


class OfferListItem(BaseModel):
    """Row in the GET /offers list view."""

    id: uuid.UUID
    client_name: str
    industry: str | None
    consulting_type: ConsultingType
    status: OfferStatus
    price_eur: Decimal | None
    created_at: datetime
    latest_version_number: int


class OfferDetail(BaseModel):
    """Full offer + its latest version, returned by GET/PATCH /offers/{id}."""

    id: uuid.UUID
    client_name: str
    industry: str | None
    consulting_type: ConsultingType
    status: OfferStatus
    price_eur: Decimal | None
    created_at: datetime
    updated_at: datetime
    version_id: uuid.UUID
    version_number: int
    version_created_at: datetime
    content: OfferContent
    co_consultant_id: uuid.UUID | None = None
    co_consultant_name: str | None = None


class OfferVersionSummary(BaseModel):
    """Row in the GET /offers/{id}/versions list view.

    `is_current` flags the version whose content is shown on the detail page
    (i.e. the highest version_number with user-renderable content).
    """

    id: uuid.UUID
    version_number: int
    revision_notes: str | None
    created_at: datetime
    is_current: bool


class OfferVersionDetail(BaseModel):
    """Read-only payload returned by GET /offers/{id}/versions/{version_number}."""

    offer_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    revision_notes: str | None
    created_at: datetime
    is_current: bool
    content: OfferContent


class OfferStatusUpdate(BaseModel):
    """Body for PATCH /offers/{id}."""

    status: OfferStatus


class OfferContentUpdate(BaseModel):
    """Body for PUT /offers/{id}/content — saves the edited offer payload as a new version."""

    content: OfferContent
    revision_notes: str | None = Field(default=None, max_length=2000)


class OfferRenderResponse(BaseModel):
    """Signed download URLs for the rendered artifacts of an offer's latest version."""

    offer_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    pptx_url: str | None = None
    word_url: str | None = None
    filename_prefix: str


# ---------------- Async-job schemas ----------------

# `complete` (matches arq's JobStatus naming) plus `failed` for when the
# worker raised. `queued`/`running` cover the in-flight states. `not_found`
# is returned for unknown job IDs (or jobs whose result already expired).
JobStatus = Literal["queued", "running", "complete", "failed", "not_found"]


class OfferJobCreateResponse(BaseModel):
    """Returned by POST /offers/jobs/generate when a job is enqueued."""

    job_id: str
    status: JobStatus


class OfferJobStatusResponse(BaseModel):
    """Returned by GET /offers/jobs/{job_id}.

    `result` is populated when status=='complete', `error` when 'failed'.
    """

    job_id: str
    status: JobStatus
    enqueue_time: datetime | None = None
    start_time: datetime | None = None
    finish_time: datetime | None = None
    result: OfferGenerateResponse | None = None
    error: str | None = None


class OfferRenderJobStatusResponse(BaseModel):
    """Returned by GET /offers/render/jobs/{job_id} — same shape as the
    generate-job status response but the result is an OfferRenderResponse."""

    job_id: str
    status: JobStatus
    enqueue_time: datetime | None = None
    start_time: datetime | None = None
    finish_time: datetime | None = None
    result: OfferRenderResponse | None = None
    error: str | None = None
