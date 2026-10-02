"""Create the initial Bronze DataJud extract table.

Revision ID: 20260921_01
Revises:
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260921_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Bronze schema and its raw DataJud extraction table."""
    op.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    op.create_table(
        "datajud_extract",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tribunal_alias", sa.Text(), nullable=False),
        sa.Column("tribunal_sigla", sa.Text(), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="bronze",
    )


def downgrade() -> None:
    """Remove the table and the now-empty Bronze schema."""
    op.drop_table("datajud_extract", schema="bronze")
    op.execute("DROP SCHEMA IF EXISTS bronze")
