"""Offer endpoints — generation, listing, detail, and status updates."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Offer
from app.schemas.offer import (
    OfferContent,
    OfferDetail,
    OfferGenerateRequest,
    OfferGenerateResponse,
    OfferListItem,
    OfferStatusUpdate,
)
from app.services.auth import CurrentUser
from app.services.offer_generator import generate_offer

router = APIRouter(prefix="/offers", tags=["offers"])


# Single-tenant assumption: every authenticated user sees every offer.
# Seed offers + early drafts have user_id=NULL because auth.users was empty
# at seed time. Switch to per-user filtering once we onboard a second berater.

# Legacy-pool guard: seed offers are stored as raw markdown
# (`content_json = {"format": "legacy_markdown", "markdown": "..."}`) and
# exist only as few-shot material. They must not appear as user-facing offers
# because they don't conform to OfferContent.
def _is_user_content(content_json: dict) -> bool:
    return isinstance(content_json, dict) and "angebot_titel" in content_json


@router.post(
    "/generate",
    response_model=OfferGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_offer_endpoint(
    request: OfferGenerateRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfferGenerateResponse:
    """Generate a new offer (status=draft) from a discovery transcript.

    Pipeline: embed input → top-K few-shot retrieval → Claude (tool-use) → persist.
    """
    try:
        user_uuid = uuid.UUID(user.id) if user.id else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user id in token: {user.id!r}",
        ) from exc

    try:
        return await generate_offer(request, user_uuid, session)
    except Exception as exc:
        logger.exception("offer generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Generation failed: {exc}",
        ) from exc


@router.get("", response_model=list[OfferListItem])
async def list_offers(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[OfferListItem]:
    """List all offers, newest first, with the latest version number per row."""
    stmt = (
        select(Offer)
        .options(selectinload(Offer.versions))
        .order_by(Offer.created_at.desc())
    )
    result = await session.execute(stmt)
    offers = result.scalars().all()

    items: list[OfferListItem] = []
    for offer in offers:
        if not offer.versions:
            continue
        latest_version = max(offer.versions, key=lambda v: v.version_number)
        if not _is_user_content(latest_version.content_json):
            continue
        items.append(
            OfferListItem(
                id=offer.id,
                client_name=offer.client_name,
                industry=offer.industry,
                consulting_type=offer.consulting_type,  # type: ignore[arg-type]
                status=offer.status,  # type: ignore[arg-type]
                price_eur=offer.price_eur,
                created_at=offer.created_at,
                latest_version_number=latest_version.version_number,
            )
        )
    return items


async def _load_detail(session: AsyncSession, offer_id: uuid.UUID) -> OfferDetail:
    """Fetch an offer with its latest version, raise 404 if missing."""
    # populate_existing=True ensures eager-loading runs even if the offer is
    # already in the session's identity map (e.g. after a status PATCH),
    # which would otherwise leave .versions as a lazy-load proxy.
    offer = await session.get(
        Offer,
        offer_id,
        options=[selectinload(Offer.versions)],
        populate_existing=True,
    )
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offer {offer_id} not found",
        )
    if not offer.versions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Offer {offer_id} has no versions",
        )

    latest = max(offer.versions, key=lambda v: v.version_number)
    if not _is_user_content(latest.content_json):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=(
                f"Offer {offer_id} is in legacy few-shot-pool format and not "
                "renderable as user content"
            ),
        )
    content = OfferContent.model_validate(latest.content_json)

    return OfferDetail(
        id=offer.id,
        client_name=offer.client_name,
        industry=offer.industry,
        consulting_type=offer.consulting_type,  # type: ignore[arg-type]
        status=offer.status,  # type: ignore[arg-type]
        price_eur=offer.price_eur,
        created_at=offer.created_at,
        updated_at=offer.updated_at,
        version_id=latest.id,
        version_number=latest.version_number,
        version_created_at=latest.created_at,
        content=content,
    )


@router.get("/{offer_id}", response_model=OfferDetail)
async def get_offer(
    offer_id: uuid.UUID,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfferDetail:
    """Return one offer with its latest version content."""
    return await _load_detail(session, offer_id)


@router.patch("/{offer_id}", response_model=OfferDetail)
async def update_offer_status(
    offer_id: uuid.UUID,
    body: OfferStatusUpdate,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfferDetail:
    """Update the status of an offer (draft|sent|won|lost)."""
    offer = await session.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offer {offer_id} not found",
        )
    offer.status = body.status
    await session.commit()
    return await _load_detail(session, offer_id)
