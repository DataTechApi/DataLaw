import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import SilverBase


class SilverDataJudSubject(SilverBase):
    """Current, deduplicated DataJud TPU subject belonging to a Silver process."""

    __tablename__ = "processo_assunto"
    __table_args__ = (
        UniqueConstraint(
            "processo_id",
            "source_hash",
            name="uq_silver_processo_assunto_processo_source_hash",
        ),
        Index("ix_silver_processo_assunto_processo_id", "processo_id"),
        Index("ix_silver_processo_assunto_codigo", "codigo"),
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
    principal: Mapped[bool | None] = mapped_column(Boolean)
