import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import SilverBase


class SilverDataJudProcess(SilverBase):
    """Current, structured representation of one Bronze DataJud extract."""

    __tablename__ = "processo"
    __table_args__ = (
        UniqueConstraint(
            "bronze_extract_id",
            name="uq_silver_processo_bronze_extract_id",
        ),
        UniqueConstraint(
            "tribunal_sigla",
            "datajud_id",
            name="uq_silver_processo_tribunal_datajud_id",
        ),
        {"schema": "silver"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bronze_extract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bronze.datajud_extract.id", ondelete="CASCADE"),
        nullable=False,
    )
    tribunal_sigla: Mapped[str] = mapped_column(Text, nullable=False)
    datajud_id: Mapped[str] = mapped_column(Text, nullable=False)
    numero_processo: Mapped[str | None] = mapped_column(Text)
    grau: Mapped[str | None] = mapped_column(Text)
    classe_codigo: Mapped[int | None] = mapped_column(Integer)
    classe_nome: Mapped[str | None] = mapped_column(Text)
    orgao_julgador_codigo: Mapped[str | None] = mapped_column(Text)
    orgao_julgador_nome: Mapped[str | None] = mapped_column(Text)
    orgao_julgador_municipio_ibge: Mapped[str | None] = mapped_column(Text)
    formato_codigo: Mapped[int | None] = mapped_column(Integer)
    formato_nome: Mapped[str | None] = mapped_column(Text)
    sistema_codigo: Mapped[int | None] = mapped_column(Integer)
    sistema_nome: Mapped[str | None] = mapped_column(Text)
    nivel_sigilo: Mapped[int | None] = mapped_column(Integer)
    data_ajuizamento: Mapped[date | None] = mapped_column(Date)
    data_hora_ultima_atualizacao: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    source_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    transformed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
