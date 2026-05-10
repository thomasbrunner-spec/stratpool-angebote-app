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

from pydantic import BaseModel, Field, field_validator

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
    def _parse_list_if_json_string(cls, v: Any) -> Any:
        """Tolerate Claude returning a nested list as a JSON string.

        Anthropic tool-use occasionally serialises complex nested arrays as
        a single string. Two flavours observed:
          1. A clean JSON array string with real newlines/quotes — `json.loads`
             handles it directly.
          2. A pseudo-JSON string where newlines are written as literal `\\n`
             and tabs as `\\t` — `json.loads` rejects it. We retry once after
             unescaping common control sequences.
        Falls back to passthrough (Pydantic raises the normal list_type error)
        if neither parse works.
        """
        if not isinstance(v, str):
            return v
        # 1) plain JSON
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            pass
        # 2) un-escape literal control sequences and retry
        try:
            unescaped = (
                v.replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace("\\r", "\r")
            )
            return json.loads(unescaped)
        except json.JSONDecodeError:
            pass
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
