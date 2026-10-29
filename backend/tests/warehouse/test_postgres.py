from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from data_law.warehouse import postgres
from data_law.warehouse.postgres import (
    PostgresWarehouse,
    ProcessCountByClass,
    ProcessSummary,
    _validate_limit,
)


class FakeResult:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.statements: list[Any] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, statement: Any) -> FakeResult:
        self.statements.append(statement)
        return FakeResult(self.rows)


def _sql(statement: Any) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.mark.parametrize("limit", [0, -1])
def test_validate_limit_rejects_non_positive_values(limit: int) -> None:
    with pytest.raises(ValueError, match="maior que zero"):
        _validate_limit(limit)


def test_validate_limit_accepts_positive_values() -> None:
    _validate_limit(1)


def test_warehouse_uses_default_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setattr(postgres, "create_session_factory", lambda: sentinel)

    assert PostgresWarehouse().session_factory is sentinel


def test_list_processes_maps_rows_to_summaries() -> None:
    updated_at = datetime(2026, 3, 20, 10, 0, tzinfo=UTC)
    session = FakeSession(
        [
            SimpleNamespace(
                datajud_id="TJSP_1",
                numero_processo="00000010220268260100",
                classe_nome="Procedimento Comum",
                orgao_julgador_nome="1ª Vara Cível",
                data_ajuizamento=date(2026, 3, 1),
                data_hora_ultima_atualizacao=updated_at,
            )
        ]
    )
    warehouse = PostgresWarehouse(lambda: session)  # type: ignore[arg-type,return-value]

    result = warehouse.list_processes(tribunal_sigla="TJSP", limit=5)

    assert result == [
        ProcessSummary(
            datajud_id="TJSP_1",
            numero_processo="00000010220268260100",
            classe_nome="Procedimento Comum",
            orgao_julgador_nome="1ª Vara Cível",
            data_ajuizamento=date(2026, 3, 1),
            atualizado_em=updated_at,
        )
    ]
    sql = _sql(session.statements[0])
    assert "silver.processo.tribunal_sigla = 'TJSP'" in sql
    assert "DESC NULLS LAST" in sql
    assert "LIMIT 5" in sql


def test_list_processes_rejects_invalid_limit_before_querying() -> None:
    session = FakeSession([])
    warehouse = PostgresWarehouse(lambda: session)  # type: ignore[arg-type,return-value]

    with pytest.raises(ValueError, match="limit"):
        warehouse.list_processes(limit=0)

    assert session.statements == []


def test_count_processes_by_class_maps_rows_to_counts() -> None:
    session = FakeSession(
        [
            SimpleNamespace(classe_nome="Procedimento Comum", total=7),
            SimpleNamespace(classe_nome="Não informada", total=2),
        ]
    )
    warehouse = PostgresWarehouse(lambda: session)  # type: ignore[arg-type,return-value]

    result = warehouse.count_processes_by_class(tribunal_sigla="TJRJ", limit=3)

    assert result == [
        ProcessCountByClass(classe_nome="Procedimento Comum", total=7),
        ProcessCountByClass(classe_nome="Não informada", total=2),
    ]
    sql = _sql(session.statements[0])
    assert "coalesce(silver.processo.classe_nome, 'Não informada')" in sql
    assert "silver.processo.tribunal_sigla = 'TJRJ'" in sql
    assert "GROUP BY" in sql
    assert "LIMIT 3" in sql


def test_count_processes_by_class_rejects_invalid_limit() -> None:
    session = FakeSession([])
    warehouse = PostgresWarehouse(lambda: session)  # type: ignore[arg-type,return-value]

    with pytest.raises(ValueError, match="limit"):
        warehouse.count_processes_by_class(limit=-5)

    assert session.statements == []
