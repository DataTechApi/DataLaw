"""Store the current payload for each DataJud process.

Revision ID: 20260921_02
Revises: 20260921_01
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260921_02"
down_revision: str | Sequence[str] | None = "20260921_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CONSTRAINT_NAME = "uq_bronze_datajud_extract_tribunal_datajud_id"


def upgrade() -> None:
    """Add process identity and content hash required for conditional merges."""
    op.add_column(
        "datajud_extract",
        sa.Column("datajud_id", sa.Text(), nullable=False),
        schema="bronze",
    )
    op.add_column(
        "datajud_extract",
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        schema="bronze",
    )
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "datajud_extract",
        ["tribunal_sigla", "datajud_id"],
        schema="bronze",
    )


def downgrade() -> None:
    """Remove conditional-merge fields from the Bronze extraction table."""
    op.drop_constraint(CONSTRAINT_NAME, "datajud_extract", schema="bronze")
    op.drop_column("datajud_extract", "payload_hash", schema="bronze")
    op.drop_column("datajud_extract", "datajud_id", schema="bronze")
