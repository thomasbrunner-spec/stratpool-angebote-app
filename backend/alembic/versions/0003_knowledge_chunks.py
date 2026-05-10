"""knowledge_chunks: domain knowledge base for offer generation.

Stores chunked + embedded reference material (Kompendium, methodology
documents) that the generate pipeline retrieves alongside the few-shot
existing offers. This is what lifts the substantive depth of generated
offers — without it, Claude has only the discovery transcript and the
anonymized few-shots, and produces generic boilerplate.

Revision ID: 0003_knowledge_chunks
Revises: 0002_consultants
Create Date: 2026-05-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_knowledge_chunks"
down_revision: str | None = "0002_consultants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge_chunks (
            id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            source      text        NOT NULL,
            chapter     text,
            title       text,
            page_from   integer,
            page_to     integer,
            ord         integer     NOT NULL,
            text        text        NOT NULL,
            token_count integer,
            embedding   vector(1024) NOT NULL,
            created_at  timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX knowledge_chunks_source_idx ON knowledge_chunks (source);")
    op.execute(
        # Same IVFFLAT setup as offer_embeddings; small lists is fine here too
        # because the corpus is bounded (single book).
        """
        CREATE INDEX knowledge_chunks_embedding_idx
        ON knowledge_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS knowledge_chunks_embedding_idx;")
    op.execute("DROP INDEX IF EXISTS knowledge_chunks_source_idx;")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks;")
