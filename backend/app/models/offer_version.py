"""OfferVersion ORM model — one row per generated revision of an offer.

content_json holds the structured offer payload returned by Claude. Word /
PowerPoint / preview-PDF artifact paths are nullable until a renderer has
written them to storage.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.offer import Offer


class OfferVersion(Base):
    __tablename__ = "offer_versions"
    __table_args__ = (
        UniqueConstraint(
            "offer_id", "version_number", name="offer_versions_offer_id_version_number_key"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    transcript: Mapped[str | None] = mapped_column(nullable=True)
    user_notes: Mapped[str | None] = mapped_column(nullable=True)
    revision_notes: Mapped[str | None] = mapped_column(nullable=True)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    word_path: Mapped[str | None] = mapped_column(nullable=True)
    pptx_path: Mapped[str | None] = mapped_column(nullable=True)
    preview_pdf_path: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )

    offer: Mapped[Offer] = relationship(back_populates="versions")
