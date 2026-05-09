"""Consultants endpoints — list and create cover-slide consultants."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Consultant
from app.schemas.consultant import ConsultantCreate, ConsultantOut
from app.services.auth import CurrentUser

router = APIRouter(prefix="/consultants", tags=["consultants"])


@router.get("", response_model=list[ConsultantOut])
async def list_consultants(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConsultantOut]:
    """List all consultants, alphabetically by name."""
    stmt = select(Consultant).order_by(Consultant.name)
    result = await session.execute(stmt)
    return [
        ConsultantOut(
            id=c.id,
            name=c.name,
            titel=c.titel,
            tel=c.tel,
            email=c.email,
            created_at=c.created_at,
        )
        for c in result.scalars().all()
    ]


@router.post("", response_model=ConsultantOut, status_code=status.HTTP_201_CREATED)
async def create_consultant(
    body: ConsultantCreate,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConsultantOut:
    """Create a new consultant. Stamps the current user as the owner."""
    try:
        owner_id = uuid.UUID(user.id) if user.id else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user id in token: {user.id!r}",
        ) from exc

    consultant = Consultant(
        name=body.name,
        titel=body.titel,
        tel=body.tel,
        email=str(body.email) if body.email else None,
        user_id=owner_id,
    )
    session.add(consultant)
    await session.flush()
    await session.commit()

    return ConsultantOut(
        id=consultant.id,
        name=consultant.name,
        titel=consultant.titel,
        tel=consultant.tel,
        email=consultant.email,
        created_at=consultant.created_at,
    )
