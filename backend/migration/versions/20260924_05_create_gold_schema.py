"""Create the Gold schema for analytical materializations.

Revision ID: 20260924_05
Revises: 20260921_04
Create Date: 2026-09-24
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260924_05"
down_revision: str | Sequence[str] | None = "20260921_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the isolated target schema used by Gold recipes."""
    op.execute("CREATE SCHEMA IF NOT EXISTS gold")


def downgrade() -> None:
    """Remove Gold only when no materialized tables remain."""
    op.execute("DROP SCHEMA IF EXISTS gold")
