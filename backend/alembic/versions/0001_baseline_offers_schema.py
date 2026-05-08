"""baseline: offers, offer_versions, offer_embeddings.

Reproduces the schema that was bootstrapped directly in Supabase Studio.
On the existing production database this revision is applied via
`alembic stamp head`; against fresh databases it creates the schema.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-08
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE offers (
            id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            client_name     text        NOT NULL,
            industry        text,
            consulting_type text        NOT NULL,
            status          text        NOT NULL DEFAULT 'draft',
            price_eur       numeric,
            user_id         uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT offers_consulting_type_check CHECK (
                consulting_type IN ('ki_strategie','ai_design_sprint','prozessberatung','workshop')
            ),
            CONSTRAINT offers_status_check CHECK (
                status IN ('draft','sent','won','lost')
            )
        )
        """
    )
    op.execute("CREATE INDEX offers_status_idx ON offers (status)")
    op.execute("CREATE INDEX offers_consulting_type_idx ON offers (consulting_type)")
    op.execute("CREATE INDEX offers_user_id_idx ON offers (user_id)")
    op.execute("CREATE INDEX offers_created_at_idx ON offers (created_at DESC)")

    op.execute(
        """
        CREATE TABLE offer_versions (
            id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            offer_id         uuid        NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            version_number   integer     NOT NULL,
            transcript       text,
            user_notes       text,
            revision_notes   text,
            content_json     jsonb       NOT NULL,
            word_path        text,
            pptx_path        text,
            preview_pdf_path text,
            created_at       timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT offer_versions_offer_id_version_number_key UNIQUE (offer_id, version_number)
        )
        """
    )
    op.execute("CREATE INDEX offer_versions_offer_id_idx ON offer_versions (offer_id)")
    op.execute("CREATE INDEX offer_versions_created_at_idx ON offer_versions (created_at DESC)")

    op.execute(
        """
        CREATE TABLE offer_embeddings (
            offer_id   uuid        PRIMARY KEY REFERENCES offers(id) ON DELETE CASCADE,
            embedding  vector(1024) NOT NULL,
            summary    text        NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX offer_embeddings_idx ON offer_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS offer_embeddings")
    op.execute("DROP TABLE IF EXISTS offer_versions")
    op.execute("DROP TABLE IF EXISTS offers")
