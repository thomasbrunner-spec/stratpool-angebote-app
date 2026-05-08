"""Offer ORM model — top-level offer record.

The table is shared with Supabase Auth (user_id -> auth.users). Status and
consulting_type are constrained at the DB level via CHECK constraints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.offer_embedding import OfferEmbedding
    from app.models.offer_version import OfferVersion


CONSULTING_TYPES = ("ki_strategie", "ai_design_sprint", "prozessberatung", "workshop")
OFFER_STATUSES = ("draft", "sent", "won", "lost")


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            f"consulting_type IN {CONSULTING_TYPES!r}",
            name="offers_consulting_type_check",
        ),
        CheckConstraint(
            f"status IN {OFFER_STATUSES!r}",
            name="offers_status_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    client_name: Mapped[str] = mapped_column(nullable=False)
    industry: Mapped[str | None] = mapped_column(nullable=True)
    consulting_type: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        nullable=False, server_default="draft", index=True
    )
    price_eur: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "auth.users.id",
            ondelete="SET NULL",
            use_alter=True,
            name="offers_user_id_fkey",
        ),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    versions: Mapped[list[OfferVersion]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        order_by="OfferVersion.version_number",
    )
    embedding: Mapped[OfferEmbedding | None] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        uselist=False,
    )
