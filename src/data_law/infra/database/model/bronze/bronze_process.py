import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import BronzeBase


class BronzeDataJudExtract(BronzeBase):
    """Latest known DataJud payload for one process in one tribunal."""

    __tablename__ = "datajud_extract"
    __table_args__ = (
        UniqueConstraint(
            "tribunal_sigla",
            "datajud_id",
            name="uq_bronze_datajud_extract_tribunal_datajud_id",
        ),
        {"schema": "bronze"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tribunal_alias: Mapped[str] = mapped_column(Text, nullable=False)
    tribunal_sigla: Mapped[str] = mapped_column(Text, nullable=False)
    datajud_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
