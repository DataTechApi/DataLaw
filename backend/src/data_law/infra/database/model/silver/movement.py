import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import SilverBase


class SilverDataJudMovement(SilverBase):
    """Current, deduplicated DataJud movement belonging to a Silver process."""

    __tablename__ = "movimento"
    __table_args__ = (
        UniqueConstraint(
            "processo_id",
            "source_hash",
            name="uq_silver_movimento_processo_source_hash",
        ),
        Index("ix_silver_movimento_processo_data_hora", "processo_id", "data_hora"),
        {"schema": "silver"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("silver.processo.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    codigo: Mapped[int | None] = mapped_column(Integer)
    nome: Mapped[str | None] = mapped_column(Text)
    data_hora: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    orgao_julgador_codigo: Mapped[str | None] = mapped_column(Text)
    orgao_julgador_nome: Mapped[str | None] = mapped_column(Text)
    complementos_tabelados: Mapped[Any | None] = mapped_column(JSONB)
