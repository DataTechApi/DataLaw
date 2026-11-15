import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_law.infra.database.base import SilverBase
from data_law.infra.database.model.silver.jurisprudencia import (
    SilverDataJudJurisprudencia,  # noqa: F401
)

PRECEDENT_DIRECTIONS = ("autor", "reu", "indefinida")


class SilverPrecedentDirection(SilverBase):
    """Curated party that a precedent's thesis benefits.

    The public sources do not state which party a thesis favors, so a curator
    records it. Precedents without a row are treated as ``indefinida``.
    """

    __tablename__ = "precedente_direcao"
    __table_args__ = (
        UniqueConstraint(
            "jurisprudencia_id",
            name="uq_silver_precedente_direcao_jurisprudencia_id",
        ),
        CheckConstraint(
            "direcao IN ('autor', 'reu', 'indefinida')",
            name="ck_silver_precedente_direcao_direcao",
        ),
        {"schema": "silver"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    jurisprudencia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("silver.jurisprudencia.id", ondelete="CASCADE"),
        nullable=False,
    )
    direcao: Mapped[str] = mapped_column(Text, nullable=False)
    curador: Mapped[str] = mapped_column(Text, nullable=False)
    curado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
