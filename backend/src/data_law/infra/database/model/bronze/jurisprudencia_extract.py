import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from data_law.infra.database.base import BronzeBase


class BronzeDataJudJurisprudenciaExtract(BronzeBase):
    """Raw payload of ingested jurisprudence and precedents."""

    __tablename__ = "jurisprudencia_extract"
    __table_args__ = (
        UniqueConstraint(
            "payload_hash",
            name="uq_bronze_jurisprudencia_payload_hash",
        ),
        {"schema": "bronze"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fonte: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
