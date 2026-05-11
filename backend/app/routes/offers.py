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
    OfferJobCreateResponse,
    OfferJobStatusResponse,
    OfferListItem,
    OfferRenderJobStatusResponse,
    OfferStatusUpdate,
    OfferVersionDetail,
    OfferVersionSummary,
)
from app.services.auth import CurrentUser
from app.services.job_queue import (
    enqueue_offer_generation,
    enqueue_offer_render,
    get_offer_job_status,
    get_render_job_status,
)

router = APIRouter(prefix="/offers", tags=["offers"])


# Single-tenant assumption: every authenticated user sees every offer.
# Seed offers + early drafts have user_id=NULL because auth.users was empty
# at seed time. Switch to per-user filtering once we onboard a second berater.

# Filter for "list/detail-renderable" content. We currently only show v2
# offers in the UI:
#   - legacy_markdown: seed pool, never user-facing
#   - v1 (8-field schema, "bestandteile" key, no "phasen"): pre-storytelling
#     drafts created before 2026-05-10. Stay in DB as history but don't
#     appear in the list since OfferContent v2 wouldn't validate them.
#   - v2 (current, "phasen" key): everything from now on.
def _is_user_content(content_json: dict) -> bool:
    return (
        isinstance(content_json, dict)
        and "angebot_titel" in content_json
        and "phasen" in content_json
    )


@router.post(
    "/jobs/generate",
    response_model=OfferJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_generate_offer(
    request: OfferGenerateRequest,
    user: CurrentUser,
) -> OfferJobCreateResponse:
    """Enqueue an async offer-generation job and return the job id immediately.

    Generation runs in the Arq worker (see `app.worker`) because the Anthropic
    streaming call with max_tokens=32k routinely exceeds the 60 s proxy
    timeout. The client polls GET /offers/jobs/{job_id} until status=='complete'.
    """
    try:
        user_uuid = uuid.UUID(user.id) if user.id else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user id in token: {user.id!r}",
        ) from exc

    try:
        job_id = await enqueue_offer_generation(request, user_uuid)
    except Exception as exc:
        logger.exception("failed to enqueue offer-generation job")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not enqueue job: {exc}",
        ) from exc

    logger.info(f"[offers] enqueued offer-generation job_id={job_id}")
    return OfferJobCreateResponse(job_id=job_id, status="queued")


@router.get("/jobs/{job_id}", response_model=OfferJobStatusResponse)
async def get_generate_offer_job(
    job_id: str,
    user: CurrentUser,
) -> OfferJobStatusResponse:
    """Poll the status of a previously enqueued offer-generation job.

    Returns `status='complete'` plus the materialised offer in `result`
    when the worker is done, `status='failed'` with `error` set when the
    worker raised, `status='not_found'` when the job id is unknown or
    its result has expired.
    """
    try:
        return await get_offer_job_status(job_id)
    except Exception as exc:
        logger.exception(f"failed to read job status for job_id={job_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not read job status: {exc}",
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


@router.get(
    "/{offer_id}/versions",
    response_model=list[OfferVersionSummary],
)
async def list_offer_versions(
    offer_id: uuid.UUID,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[OfferVersionSummary]:
    """List all user-renderable versions of an offer, newest first.

    Legacy v1 versions are filtered out — they would not validate against
    the OfferContent schema and aren't viewable in the UI. `is_current`
    marks the highest version_number that's user-renderable.
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

    user_versions = [v for v in offer.versions if _is_user_content(v.content_json)]
    if not user_versions:
        return []

    current_version_number = max(v.version_number for v in user_versions)
    user_versions.sort(key=lambda v: v.version_number, reverse=True)

    return [
        OfferVersionSummary(
            id=v.id,
            version_number=v.version_number,
            revision_notes=v.revision_notes,
            created_at=v.created_at,
            is_current=v.version_number == current_version_number,
        )
        for v in user_versions
    ]


@router.get(
    "/{offer_id}/versions/{version_number}",
    response_model=OfferVersionDetail,
)
async def get_offer_version(
    offer_id: uuid.UUID,
    version_number: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfferVersionDetail:
    """Return the structured content of a specific version of an offer."""
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

    target = next(
        (v for v in offer.versions if v.version_number == version_number),
        None,
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offer {offer_id} has no version {version_number}",
        )
    if not _is_user_content(target.content_json):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=(
                f"Version {version_number} of offer {offer_id} is in legacy "
                "format and not renderable as user content"
            ),
        )

    user_versions = [v for v in offer.versions if _is_user_content(v.content_json)]
    current_version_number = max(v.version_number for v in user_versions)

    return OfferVersionDetail(
        offer_id=offer.id,
        version_id=target.id,
        version_number=target.version_number,
        revision_notes=target.revision_notes,
        created_at=target.created_at,
        is_current=target.version_number == current_version_number,
        content=OfferContent.model_validate(target.content_json),
    )


@router.post(
    "/{offer_id}/render",
    response_model=OfferJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_render_offer_endpoint(
    offer_id: uuid.UUID,
    user: CurrentUser,
    format: Annotated[
        str, Query(pattern="^(pptx|word)$", description="Render target format")
    ] = "pptx",
    force: Annotated[
        bool,
        Query(description="If true, ignore the cached artifact and render anew"),
    ] = False,
) -> OfferJobCreateResponse:
    """Enqueue a render job for the offer's latest version and return its id.

    The actual render (Anthropic code-execution) takes 2–5 minutes and is
    well past the Coolify/Traefik 60 s proxy timeout, so it runs in the
    Arq worker. The client polls GET /offers/render/jobs/{job_id} until
    status=='complete'.

    `force=true` re-runs the skill even if a cached pptx/word artifact
    exists for this version. Used by the skill-iteration workflow.
    """
    try:
        job_id = await enqueue_offer_render(offer_id, format, force=force)
    except Exception as exc:
        logger.exception("failed to enqueue offer-render job")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not enqueue render job: {exc}",
        ) from exc

    logger.info(
        f"[offers] enqueued offer-render job_id={job_id} "
        f"offer_id={offer_id} format={format} force={force}"
    )
    return OfferJobCreateResponse(job_id=job_id, status="queued")


@router.get(
    "/render/jobs/{job_id}",
    response_model=OfferRenderJobStatusResponse,
)
async def get_render_offer_job(
    job_id: str,
    user: CurrentUser,
) -> OfferRenderJobStatusResponse:
    """Poll the status of a previously enqueued render job.

    Returns `status='complete'` plus the OfferRenderResponse in `result`
    (with signed pptx/word URLs) when the worker is done.
    """
    try:
        return await get_render_job_status(job_id)
    except Exception as exc:
        logger.exception(f"failed to read render job status for job_id={job_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not read render job status: {exc}",
        ) from exc
