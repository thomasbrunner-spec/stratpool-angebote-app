"""KnowledgeChunk ORM model — chunked + embedded reference material.

Used by the offer generator to retrieve relevant methodology / domain
knowledge alongside the few-shot pool of existing offers.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source: Mapped[str] = mapped_column(nullable=False, index=True)
    chapter: Mapped[str | None] = mapped_column(nullable=True)
    title: Mapped[str | None] = mapped_column(nullable=True)
    page_from: Mapped[int | None] = mapped_column(nullable=True)
    page_to: Mapped[int | None] = mapped_column(nullable=True)
    ord: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    token_count: Mapped[int | None] = mapped_column(nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
