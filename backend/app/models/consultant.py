"""Consultant ORM model — master data for cover-slide consultants.

Each row represents one person whose name/title/contact can be picked as the
secondary consultant on an offer's cover slide. user_id is nullable so we can
seed shared records during the single-tenant phase.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.offer import Offer


class Consultant(Base):
    __tablename__ = "consultants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(nullable=False)
    titel: Mapped[str | None] = mapped_column(nullable=True)
    tel: Mapped[str | None] = mapped_column(nullable=True)
    email: Mapped[str | None] = mapped_column(nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "auth.users.id",
            ondelete="SET NULL",
            use_alter=True,
            name="consultants_user_id_fkey",
        ),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    offers: Mapped[list[Offer]] = relationship(back_populates="co_consultant")
