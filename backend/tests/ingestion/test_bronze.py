import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from data_law.infra.database.model.bronze.bronze_process import BronzeDataJudExtract
from data_law.infra.database.session import create_session_factory
from data_law.ingestion.bronze import (
    BronzeProcessingError,
    _read_process_payloads,
    payload_hash,
    process_raw_file,
)


class FakeResult:
    def __init__(self, value: object | None) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object | None:
        return self.value


class FakeSession:
    def __init__(self, results: list[object | None]) -> None:
        self.results = results
        self.statements: list[object] = []
        self.transactions = 0

    @contextmanager
    def begin(self):
        self.transactions += 1
        yield self

    def execute(self, statement: object) -> FakeResult:
        self.statements.append(statement)
        return FakeResult(self.results.pop(0))


def _write_response(file_path: Path, processes: list[dict[str, object]]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(
            {"hits": {"hits": [{"_source": process} for process in processes]}},
        ),
        encoding="utf-8",
    )


def test_payload_hash_is_stable_for_key_order() -> None:
    assert payload_hash({"id": "1234", "movimentos": [1, 2]}) == payload_hash(
        {"movimentos": [1, 2], "id": "1234"}
    )


def test_process_raw_file_builds_one_upsert_per_process(tmp_path: Path) -> None:
    raw_directory = tmp_path / "data" / "raw"
    file_path = raw_directory / "tjsp" / "response.json"
    _write_response(
        file_path,
        [
            {"id": "1234", "movimentos": [{"codigo": 22}]},
            {"id": "5678", "movimentos": [{"codigo": 246}]},
        ],
    )
    session = FakeSession(["inserted", None])

    result = process_raw_file(file_path, session, raw_directory)

    assert result.source_file == "data/raw/tjsp/response.json"
    assert result.total == 2
    assert result.changed == 1
    assert result.unchanged == 1
    assert session.transactions == 1
    assert len(session.statements) == 2


def test_invalid_process_without_datajud_id_stops_file_processing(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"
    file_path = raw_directory / "tjsp" / "invalid.json"
    _write_response(file_path, [{"movimentos": []}])

    with pytest.raises(BronzeProcessingError, match="_source.id"):
        _read_process_payloads(file_path)


@pytest.mark.integration
def test_postgres_merge_updates_only_changed_process(tmp_path: Path) -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL não configurada para teste de integração")

    raw_directory = tmp_path / "data" / "raw"
    file_path = raw_directory / "tjsp" / "response.json"
    datajud_id = f"pytest-{uuid.uuid4()}"
    session_factory = create_session_factory()

    try:
        _write_response(
            file_path,
            [
                {
                    "id": datajud_id,
                    "movimentos": [{"codigo": item} for item in range(10)],
                }
            ],
        )
        with session_factory() as session:
            assert process_raw_file(file_path, session, raw_directory).changed == 1

        with session_factory() as session:
            assert process_raw_file(file_path, session, raw_directory).changed == 0

        _write_response(
            file_path,
            [
                {
                    "id": datajud_id,
                    "movimentos": [{"codigo": item} for item in range(12)],
                }
            ],
        )
        with session_factory() as session:
            assert process_raw_file(file_path, session, raw_directory).changed == 1
            stored = session.scalar(
                select(BronzeDataJudExtract).where(
                    BronzeDataJudExtract.tribunal_sigla == "TJSP",
                    BronzeDataJudExtract.datajud_id == datajud_id,
                )
            )

        assert stored is not None
        assert len(stored.payload["movimentos"]) == 12
    finally:
        with session_factory() as session:
            with session.begin():
                session.execute(
                    delete(BronzeDataJudExtract).where(
                        BronzeDataJudExtract.tribunal_sigla == "TJSP",
                        BronzeDataJudExtract.datajud_id == datajud_id,
                    )
                )
