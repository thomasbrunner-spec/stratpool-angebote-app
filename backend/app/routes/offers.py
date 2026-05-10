"""Offer endpoints — generation, listing, detail, and status updates."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Offer, OfferVersion
from app.schemas.offer import (
    OfferContent,
    OfferContentUpdate,
    OfferDetail,
    OfferGenerateRequest,
    OfferGenerateResponse,
    OfferListItem,
    OfferRenderResponse,
    OfferStatusUpdate,
)
from app.services.auth import CurrentUser
from app.services.offer_generator import generate_offer
from app.services.render_via_skill import RenderError, render_offer_via_skill
from app.services.storage import render_path, signed_url, upload_render

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
        options=[selectinload(Offer.versions), selectinload(Offer.co_consultant)],
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
        co_consultant_id=offer.co_consultant_id,
        co_consultant_name=offer.co_consultant.name if offer.co_consultant else None,
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


@router.put("/{offer_id}/content", response_model=OfferDetail)
async def update_offer_content(
    offer_id: uuid.UUID,
    body: OfferContentUpdate,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfferDetail:
    """Persist edited offer content as a new version.

    Each save creates `latest.version_number + 1` so the original generate
    output stays reproducible and stale render artifacts (pptx_path /
    word_path) don't carry over to the new version — re-rendering after an
    edit always produces a fresh artifact.
    """
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
            detail=f"Offer {offer_id} has no versions to base an edit on",
        )

    latest = max(offer.versions, key=lambda v: v.version_number)
    if not _is_user_content(latest.content_json):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Legacy pool entry is not editable as user content",
        )

    new_version = OfferVersion(
        offer_id=offer.id,
        version_number=latest.version_number + 1,
        transcript=latest.transcript,
        user_notes=latest.user_notes,
        revision_notes=body.revision_notes,
        content_json=body.content.model_dump(mode="json"),
    )
    session.add(new_version)
    await session.commit()
    return await _load_detail(session, offer_id)


_FORMAT_MIME = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_FORMAT_SUFFIX = {"pptx": "pptx", "word": "docx"}
_SIGNED_URL_TTL_SECONDS = 3600


def _filename_prefix(client_name: str) -> str:
    """`Angebot - <kunde>` with reserved chars stripped, safe for HTTP headers."""
    safe = "".join(c for c in client_name if c.isalnum() or c in " .-_").strip()
    return f"Angebot - {safe or 'Angebot'}"


@router.post("/{offer_id}/render", response_model=OfferRenderResponse)
async def render_offer_endpoint(
    offer_id: uuid.UUID,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[
        str, Query(pattern="^(pptx|word)$", description="Render target format")
    ] = "pptx",
) -> OfferRenderResponse:
    """Render the offer's latest version to PPT or Word.

    Cached: each format is generated once per version and stored in Supabase.
    Subsequent calls reuse the cached file and only refresh the signed URL.
    """
    offer = await session.get(
        Offer,
        offer_id,
        options=[selectinload(Offer.versions), selectinload(Offer.co_consultant)],
        populate_existing=True,
    )
    if offer is None:
        raise HTTPException(status_code=404, detail=f"Offer {offer_id} not found")
    if not offer.versions:
        raise HTTPException(status_code=409, detail="Offer has no versions")

    latest = max(offer.versions, key=lambda v: v.version_number)
    if not _is_user_content(latest.content_json):
        raise HTTPException(status_code=410, detail="Legacy pool entry is not renderable")

    # Select the cached path attribute and per-format MIME.
    path_attr = "pptx_path" if format == "pptx" else "word_path"
    cached = getattr(latest, path_attr)

    if not cached:
        try:
            payload = await render_offer_via_skill(
                fmt=format,  # type: ignore[arg-type]
                transcript=latest.transcript or "",
                user_notes=latest.user_notes,
                client_name=offer.client_name,
                industry=offer.industry,
                consulting_type=offer.consulting_type,
                price_eur=offer.price_eur,
                co_consultant=offer.co_consultant,
            )
        except RenderError as exc:
            logger.exception(f"skill-render failed (format={format})")
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception(f"skill-render unexpected error (format={format})")
            raise HTTPException(status_code=500, detail=f"Render failed: {exc}") from exc
        storage_path = render_path(
            str(offer_id), latest.version_number, _FORMAT_SUFFIX[format]
        )
        await upload_render(storage_path, payload, _FORMAT_MIME[format])
        setattr(latest, path_attr, storage_path)
        await session.commit()

    pptx_url = (
        await signed_url(latest.pptx_path, expires_in=_SIGNED_URL_TTL_SECONDS)
        if latest.pptx_path
        else None
    )
    word_url = (
        await signed_url(latest.word_path, expires_in=_SIGNED_URL_TTL_SECONDS)
        if latest.word_path
        else None
    )

    return OfferRenderResponse(
        offer_id=offer.id,
        version_id=latest.id,
        version_number=latest.version_number,
        pptx_url=pptx_url,
        word_url=word_url,
        filename_prefix=_filename_prefix(offer.client_name),
    )
