"""Store the DataJud incremental-ingestion checkpoint.

Revision ID: 20260921_03
Revises: 20260921_02
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260921_03"
down_revision: str | Sequence[str] | None = "20260921_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the per-tribunal checkpoint table."""
    op.create_table(
        "datajud_ingestion_state",
        sa.Column("tribunal_alias", sa.Text(), nullable=False),
        sa.Column("tribunal_sigla", sa.Text(), nullable=False),
        sa.Column("last_successful_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tribunal_alias"),
        schema="bronze",
    )


def downgrade() -> None:
    """Remove the incremental-ingestion checkpoint table."""
    op.drop_table("datajud_ingestion_state", schema="bronze")
