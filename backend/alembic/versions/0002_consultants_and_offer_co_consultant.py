"""consultants table + offers.co_consultant_id FK.

Adds a per-consultant master table so the cover slide can pick a secondary
consultant per offer instead of reading them from .env. user_id is nullable
to allow shared records during the single-tenant phase.

Revision ID: 0002_consultants
Revises: 0001_baseline
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_consultants"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE consultants (
            id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            name       text        NOT NULL,
            titel      text,
            tel        text,
            email      text,
            user_id    uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX consultants_user_id_idx ON consultants (user_id)")
    op.execute("CREATE INDEX consultants_name_idx ON consultants (name)")

    op.execute(
        "ALTER TABLE offers "
        "ADD COLUMN co_consultant_id uuid REFERENCES consultants(id) ON DELETE SET NULL"
    )
    op.execute("CREATE INDEX offers_co_consultant_id_idx ON offers (co_consultant_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS offers_co_consultant_id_idx")
    op.execute("ALTER TABLE offers DROP COLUMN IF EXISTS co_consultant_id")
    op.execute("DROP TABLE IF EXISTS consultants")
