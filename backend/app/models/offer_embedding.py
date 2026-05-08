"""OfferEmbedding ORM model — one Voyage embedding per offer for retrieval.

Dimension is fixed at 1024 to match voyage-3-large. The ivfflat index lives
on the DB side (vector_cosine_ops). The summary text is what the embedding
was computed from; keeping it lets us re-embed without re-summarizing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.offer import Offer


VOYAGE_EMBEDDING_DIM = 1024


class OfferEmbedding(Base):
    __tablename__ = "offer_embeddings"

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(VOYAGE_EMBEDDING_DIM), nullable=False
    )
    summary: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    offer: Mapped[Offer] = relationship(back_populates="embedding")
