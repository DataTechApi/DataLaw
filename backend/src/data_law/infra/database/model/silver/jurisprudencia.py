import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import SilverBase
from data_law.infra.database.model.bronze.jurisprudencia_extract import (
    BronzeDataJudJurisprudenciaExtract,  # noqa: F401
)


class SilverDataJudJurisprudencia(SilverBase):
    """Normalized, deduplicated jurisprudence or precedent.

    Associated with TPU subjects.
    """

    __tablename__ = "jurisprudencia"
    __table_args__ = (
        UniqueConstraint(
            "source_hash",
            name="uq_silver_jurisprudencia_source_hash",
        ),
        Index("ix_silver_jurisprudencia_assunto_codigo", "assunto_codigo"),
        Index("ix_silver_jurisprudencia_tribunal", "tribunal_sigla"),
        {"schema": "silver"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bronze_extract_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bronze.jurisprudencia_extract.id", ondelete="SET NULL"),
        nullable=True,
    )
    tribunal_sigla: Mapped[str] = mapped_column(Text, nullable=False)
    numero_processo: Mapped[str | None] = mapped_column(Text)
    identificador_precedente: Mapped[str | None] = mapped_column(Text)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    ementa: Mapped[str] = mapped_column(Text, nullable=False)
    tese: Mapped[str | None] = mapped_column(Text)
    relator: Mapped[str | None] = mapped_column(Text)
    data_julgamento: Mapped[date | None] = mapped_column(Date)
    assunto_codigo: Mapped[int | None] = mapped_column(Integer)
    assunto_nome: Mapped[str | None] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
