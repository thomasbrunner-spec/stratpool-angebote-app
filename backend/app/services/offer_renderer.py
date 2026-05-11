"""Offer-render orchestration — same code path for sync endpoint and worker.

The Anthropic skill-driven render typically takes 2–5 minutes (longer than
Coolify's 60-s proxy timeout), so this lives behind an Arq job. The function
below is the actual orchestration logic; both the (now-enqueueing) endpoint
and the worker entry point call it.

Cache behaviour: each (offer_version, format) is rendered at most once. The
artifact path is stored on the OfferVersion row (`pptx_path` / `word_path`);
subsequent calls just refresh the signed download URL.
"""

from __future__ import annotations

import uuid
from typing import Literal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Offer
from app.schemas.offer import OfferRenderResponse
from app.services.render_via_skill import RenderError, render_offer_via_skill
from app.services.storage import render_path, signed_url, upload_render

RenderFormat = Literal["pptx", "word"]

_FORMAT_MIME: dict[RenderFormat, str] = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_FORMAT_SUFFIX: dict[RenderFormat, str] = {"pptx": "pptx", "word": "docx"}
_SIGNED_URL_TTL_SECONDS = 3600


class OfferRenderInputError(Exception):
    """Raised for user-correctable problems (offer missing, legacy schema)."""


def _is_user_content(content_json: dict) -> bool:
    """Render only v2 (storytelling) versions — legacy seed/v1 content is not user-facing."""
    return (
        isinstance(content_json, dict)
        and "angebot_titel" in content_json
        and "phasen" in content_json
    )


def _filename_prefix(client_name: str) -> str:
    """`Angebot - <kunde>` with reserved chars stripped, safe for HTTP headers."""
    safe = "".join(c for c in client_name if c.isalnum() or c in " .-_").strip()
    return f"Angebot - {safe or 'Angebot'}"


async def perform_offer_render(
    session: AsyncSession,
    offer_id: uuid.UUID,
    fmt: RenderFormat,
) -> OfferRenderResponse:
    """Render an offer's latest version to PPT or Word (cached per version)."""
    offer = await session.get(
        Offer,
        offer_id,
        options=[selectinload(Offer.versions), selectinload(Offer.co_consultant)],
        populate_existing=True,
    )
    if offer is None:
        raise OfferRenderInputError(f"Offer {offer_id} not found")
    if not offer.versions:
        raise OfferRenderInputError(f"Offer {offer_id} has no versions")

    latest = max(offer.versions, key=lambda v: v.version_number)
    if not _is_user_content(latest.content_json):
        raise OfferRenderInputError(
            f"Offer {offer_id} is in legacy format and not renderable"
        )

    path_attr = "pptx_path" if fmt == "pptx" else "word_path"
    cached = getattr(latest, path_attr)

    if not cached:
        logger.info(
            f"[render] starting skill render offer_id={offer_id} "
            f"version={latest.version_number} format={fmt}"
        )
        try:
            payload = await render_offer_via_skill(
                fmt=fmt,
                transcript=latest.transcript or "",
                user_notes=latest.user_notes,
                client_name=offer.client_name,
                industry=offer.industry,
                consulting_type=offer.consulting_type,
                price_eur=offer.price_eur,
                co_consultant=offer.co_consultant,
                offer_content_json=latest.content_json,
            )
        except RenderError:
            logger.exception(f"[render] skill render failed (format={fmt})")
            raise
        storage_path = render_path(str(offer_id), latest.version_number, _FORMAT_SUFFIX[fmt])
        await upload_render(storage_path, payload, _FORMAT_MIME[fmt])
        setattr(latest, path_attr, storage_path)
        await session.commit()
        logger.info(
            f"[render] skill render done offer_id={offer_id} "
            f"version={latest.version_number} format={fmt} -> {storage_path}"
        )

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
