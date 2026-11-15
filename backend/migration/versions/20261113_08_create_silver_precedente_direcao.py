"""Create silver.precedente_direcao for curated thesis directions.

Revision ID: 20261113_08
Revises: 20261019_07
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261113_08"
down_revision: str | Sequence[str] | None = "20261019_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "precedente_direcao",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jurisprudencia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direcao", sa.Text(), nullable=False),
        sa.Column("curador", sa.Text(), nullable=False),
        sa.Column(
            "curado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "direcao IN ('autor', 'reu', 'indefinida')",
            name="ck_silver_precedente_direcao_direcao",
        ),
        sa.ForeignKeyConstraint(
            ["jurisprudencia_id"],
            ["silver.jurisprudencia.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "jurisprudencia_id",
            name="uq_silver_precedente_direcao_jurisprudencia_id",
        ),
        schema="silver",
    )


def downgrade() -> None:
    op.drop_table("precedente_direcao", schema="silver")
