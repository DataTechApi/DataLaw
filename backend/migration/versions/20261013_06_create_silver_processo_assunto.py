"""Create the Silver process subject table (processo_assunto).

Revision ID: 20261013_06
Revises: 20260924_05
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261013_06"
down_revision: str | Sequence[str] | None = "20260924_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create silver.processo_assunto table for TPU subject normalization."""
    op.create_table(
        "processo_assunto",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("codigo", sa.Integer(), nullable=True),
        sa.Column("nome", sa.Text(), nullable=True),
        sa.Column("principal", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["silver.processo.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "processo_id",
            "source_hash",
            name="uq_silver_processo_assunto_processo_source_hash",
        ),
        schema="silver",
    )
    op.create_index(
        "ix_silver_processo_assunto_processo_id",
        "processo_assunto",
        ["processo_id"],
        unique=False,
        schema="silver",
    )
    op.create_index(
        "ix_silver_processo_assunto_codigo",
        "processo_assunto",
        ["codigo"],
        unique=False,
        schema="silver",
    )


def downgrade() -> None:
    """Drop silver.processo_assunto table and its indexes."""
    op.drop_index(
        "ix_silver_processo_assunto_codigo",
        table_name="processo_assunto",
        schema="silver",
    )
    op.drop_index(
        "ix_silver_processo_assunto_processo_id",
        table_name="processo_assunto",
        schema="silver",
    )
    op.drop_table("processo_assunto", schema="silver")
