"""Pydantic schemas for the consultants resource."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ConsultantCreate(BaseModel):
    """Body for POST /consultants."""

    name: str = Field(min_length=1, max_length=200)
    titel: str | None = Field(default=None, max_length=200)
    tel: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None


class ConsultantOut(BaseModel):
    """Read shape returned by GET /consultants."""

    id: uuid.UUID
    name: str
    titel: str | None
    tel: str | None
    email: str | None
    created_at: datetime
