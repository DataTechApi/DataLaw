from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, select

from data_law.infra.database.model.silver.process import SilverDataJudProcess
from data_law.infra.database.session import SessionFactory, create_session_factory


@dataclass(frozen=True)
class ProcessSummary:
    datajud_id: str
    numero_processo: str | None
    classe_nome: str | None
    orgao_julgador_nome: str | None
    data_ajuizamento: date | None
    atualizado_em: datetime | None


@dataclass(frozen=True)
class ProcessCountByClass:
    classe_nome: str
    total: int


class PostgresWarehouse:
    """Read-only analytical queries over the Silver PostgreSQL layer."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self.session_factory = session_factory or create_session_factory()

    def list_processes(
        self,
        *,
        tribunal_sigla: str = "TJSP",
        limit: int = 10,
    ) -> list[ProcessSummary]:
        """Return the most recently updated processes for one tribunal."""
        _validate_limit(limit)

        statement = (
            select(
                SilverDataJudProcess.datajud_id,
                SilverDataJudProcess.numero_processo,
                SilverDataJudProcess.classe_nome,
                SilverDataJudProcess.orgao_julgador_nome,
                SilverDataJudProcess.data_ajuizamento,
                SilverDataJudProcess.data_hora_ultima_atualizacao,
            )
            .where(SilverDataJudProcess.tribunal_sigla == tribunal_sigla)
            .order_by(
                SilverDataJudProcess.data_hora_ultima_atualizacao.desc().nulls_last(),
                SilverDataJudProcess.datajud_id,
            )
            .limit(limit)
        )

        with self.session_factory() as session:
            rows = session.execute(statement).all()

        return [
            ProcessSummary(
                datajud_id=row.datajud_id,
                numero_processo=row.numero_processo,
                classe_nome=row.classe_nome,
                orgao_julgador_nome=row.orgao_julgador_nome,
                data_ajuizamento=row.data_ajuizamento,
                atualizado_em=row.data_hora_ultima_atualizacao,
            )
            for row in rows
        ]

    def count_processes_by_class(
        self,
        *,
        tribunal_sigla: str = "TJSP",
        limit: int = 10,
    ) -> list[ProcessCountByClass]:
        """Return the most frequent procedural classes for one tribunal."""
        _validate_limit(limit)
        classe_nome = func.coalesce(
            SilverDataJudProcess.classe_nome,
            "Não informada",
        ).label("classe_nome")
        statement = (
            select(classe_nome, func.count().label("total"))
            .where(SilverDataJudProcess.tribunal_sigla == tribunal_sigla)
            .group_by(classe_nome)
            .order_by(func.count().desc(), classe_nome)
            .limit(limit)
        )

        with self.session_factory() as session:
            rows = session.execute(statement).all()

        return [
            ProcessCountByClass(classe_nome=row.classe_nome, total=row.total)
            for row in rows
        ]


def _validate_limit(limit: int) -> None:
    if limit <= 0:
        raise ValueError("limit deve ser maior que zero")
