from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import BronzeBase


class BronzeDataJudIngestionState(BronzeBase):
    """Last fully completed DataJud ingestion for one tribunal."""

    __tablename__ = "datajud_ingestion_state"

    tribunal_alias: Mapped[str] = mapped_column(Text, primary_key=True)
    tribunal_sigla: Mapped[str] = mapped_column(Text, nullable=False)
    last_successful_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
