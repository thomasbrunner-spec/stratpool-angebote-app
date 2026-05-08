"""Pydantic schemas for the offer generation pipeline.

The `OfferContent` schema is the single source of truth for the structured
JSON Claude returns and that gets persisted in `offer_versions.content_json`.
The same schema drives the Anthropic tool-use spec — keep them in sync.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.offer import CONSULTING_TYPES

ConsultingType = Literal["ki_strategie", "ai_design_sprint", "prozessberatung", "workshop"]
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


class OfferContentBestandteil(BaseModel):
    """One Leistungs-Bestandteil — variable count per offer."""

    titel: str = Field(min_length=1, max_length=200)
    beschreibung: str = Field(min_length=1)


class OfferContent(BaseModel):
    """Structured offer payload, one row per OfferVersion.content_json."""

    angebot_titel: str = Field(min_length=1, max_length=200)
    client_name: str = Field(min_length=1, max_length=200)
    ausgangssituation: str = Field(min_length=1)
    leistungsumfang_intro: str = Field(min_length=1)
    bestandteile: list[OfferContentBestandteil] = Field(min_length=1, max_length=8)
    leistungserbringung: str = Field(min_length=1)
    investition: str = Field(min_length=1)
    rahmenbedingungen: str = Field(min_length=1)


class OfferGenerateResponse(BaseModel):
    """Response returned by POST /api/v1/offers/generate."""

    offer_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    content: OfferContent
    retrieved_offer_ids: list[uuid.UUID] = Field(
        description="IDs of the Bestandsangebote used as few-shots, ordered by similarity"
    )
    created_at: datetime
