"""Create bronze and silver jurisprudence and precedent tables.

Revision ID: 20261019_07
Revises: 20261013_06
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261019_07"
down_revision: str | Sequence[str] | None = "20261013_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jurisprudencia_extract",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fonte", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payload_hash", name="uq_bronze_jurisprudencia_payload_hash"),
        schema="bronze",
    )

    op.create_table(
        "jurisprudencia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bronze_extract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tribunal_sigla", sa.Text(), nullable=False),
        sa.Column("numero_processo", sa.Text(), nullable=True),
        sa.Column("identificador_precedente", sa.Text(), nullable=True),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("ementa", sa.Text(), nullable=False),
        sa.Column("tese", sa.Text(), nullable=True),
        sa.Column("relator", sa.Text(), nullable=True),
        sa.Column("data_julgamento", sa.Date(), nullable=True),
        sa.Column("assunto_codigo", sa.Integer(), nullable=True),
        sa.Column("assunto_nome", sa.Text(), nullable=True),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["bronze_extract_id"],
            ["bronze.jurisprudencia_extract.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_hash", name="uq_silver_jurisprudencia_source_hash"),
        schema="silver",
    )
    op.create_index(
        "ix_silver_jurisprudencia_assunto_codigo",
        "jurisprudencia",
        ["assunto_codigo"],
        unique=False,
        schema="silver",
    )
    op.create_index(
        "ix_silver_jurisprudencia_tribunal",
        "jurisprudencia",
        ["tribunal_sigla"],
        unique=False,
        schema="silver",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_silver_jurisprudencia_tribunal",
        table_name="jurisprudencia",
        schema="silver",
    )
    op.drop_index(
        "ix_silver_jurisprudencia_assunto_codigo",
        table_name="jurisprudencia",
        schema="silver",
    )
    op.drop_table("jurisprudencia", schema="silver")
    op.drop_table("jurisprudencia_extract", schema="bronze")
