"""Create the Silver SCD1 process and movement tables.

Revision ID: 20260921_04
Revises: 20260921_03
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260921_04"
down_revision: str | Sequence[str] | None = "20260921_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the normalized current-state Silver layer."""
    op.execute("CREATE SCHEMA IF NOT EXISTS silver")
    op.create_table(
        "processo",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "bronze_extract_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("tribunal_sigla", sa.Text(), nullable=False),
        sa.Column("datajud_id", sa.Text(), nullable=False),
        sa.Column("numero_processo", sa.Text(), nullable=True),
        sa.Column("grau", sa.Text(), nullable=True),
        sa.Column("classe_codigo", sa.Integer(), nullable=True),
        sa.Column("classe_nome", sa.Text(), nullable=True),
        sa.Column("orgao_julgador_codigo", sa.Text(), nullable=True),
        sa.Column("orgao_julgador_nome", sa.Text(), nullable=True),
        sa.Column("orgao_julgador_municipio_ibge", sa.Text(), nullable=True),
        sa.Column("formato_codigo", sa.Integer(), nullable=True),
        sa.Column("formato_nome", sa.Text(), nullable=True),
        sa.Column("sistema_codigo", sa.Integer(), nullable=True),
        sa.Column("sistema_nome", sa.Text(), nullable=True),
        sa.Column("nivel_sigilo", sa.Integer(), nullable=True),
        sa.Column("data_ajuizamento", sa.Date(), nullable=True),
        sa.Column("data_hora_ultima_atualizacao", sa.DateTime(timezone=True)),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("source_payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "source_extracted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("transformed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["bronze_extract_id"],
            ["bronze.datajud_extract.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "bronze_extract_id",
            name="uq_silver_processo_bronze_extract_id",
        ),
        sa.UniqueConstraint(
            "tribunal_sigla",
            "datajud_id",
            name="uq_silver_processo_tribunal_datajud_id",
        ),
        schema="silver",
    )
    op.create_table(
        "movimento",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("codigo", sa.Integer(), nullable=True),
        sa.Column("nome", sa.Text(), nullable=True),
        sa.Column("data_hora", sa.DateTime(timezone=True), nullable=True),
        sa.Column("orgao_julgador_codigo", sa.Text(), nullable=True),
        sa.Column("orgao_julgador_nome", sa.Text(), nullable=True),
        sa.Column(
            "complementos_tabelados",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["silver.processo.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "processo_id",
            "source_hash",
            name="uq_silver_movimento_processo_source_hash",
        ),
        schema="silver",
    )
    op.create_index(
        "ix_silver_movimento_processo_data_hora",
        "movimento",
        ["processo_id", "data_hora"],
        unique=False,
        schema="silver",
    )


def downgrade() -> None:
    """Remove the Silver tables and their now-empty schema."""
    op.drop_index(
        "ix_silver_movimento_processo_data_hora",
        table_name="movimento",
        schema="silver",
    )
    op.drop_table("movimento", schema="silver")
    op.drop_table("processo", schema="silver")
    op.execute("DROP SCHEMA IF EXISTS silver")
