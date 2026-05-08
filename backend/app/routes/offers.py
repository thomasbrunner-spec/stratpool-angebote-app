"""Offer endpoints — generation, listing, and version retrieval."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.offer import OfferGenerateRequest, OfferGenerateResponse
from app.services.auth import CurrentUser
from app.services.offer_generator import generate_offer

router = APIRouter(prefix="/offers", tags=["offers"])


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
