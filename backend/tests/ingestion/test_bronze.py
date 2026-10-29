import gzip
import json
import os
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import delete, select
from sqlalchemy.dialects import postgresql

from data_law.infra.database.model.bronze.bronze_process import BronzeDataJudExtract
from data_law.infra.database.session import create_session_factory
from data_law.ingestion import bronze
from data_law.ingestion.bronze import (
    BronzeProcessingError,
    ProcessedFile,
    _metadata_for_file,
    _read_process_payloads,
    payload_hash,
    process_raw_directory,
    process_raw_file,
)
from data_law.transformation.silver import SilverSyncReport


class FakeResult:
    def __init__(self, value: object | None) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object | None:
        return self.value


class FakeSession:
    def __init__(self, results: list[object | None]) -> None:
        self.results = results
        self.statements: list[Any] = []
        self.transactions = 0

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

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


def test_read_process_payloads_reads_gzip_files(tmp_path: Path) -> None:
    file_path = tmp_path / "page.json.gz"
    with gzip.open(file_path, "wt", encoding="utf-8") as file:
        json.dump({"hits": {"hits": [{"_source": {"id": "1234"}}]}}, file)

    assert _read_process_payloads(file_path) == [{"id": "1234"}]


@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("{not json", "JSON inválido"),
        ("[]", "objeto JSON"),
        ('{"hits": []}', "hits.hits"),
        ('{"hits": {"hits": {}}}', "hits.hits"),
        ('{"hits": {"hits": ["texto"]}}', "sem _source válido"),
        ('{"hits": {"hits": [{"_source": []}]}}', "sem _source válido"),
        ('{"hits": {"hits": [{"_source": {"id": "   "}}]}}', "_source.id"),
        ('{"hits": {"hits": [{"_source": {"id": 123}}]}}', "_source.id"),
    ],
)
def test_read_process_payloads_rejects_malformed_responses(
    tmp_path: Path,
    content: str,
    error: str,
) -> None:
    file_path = tmp_path / "page.json"
    file_path.write_text(content, encoding="utf-8")

    with pytest.raises(BronzeProcessingError, match=error):
        _read_process_payloads(file_path)


def test_metadata_for_file_resolves_tribunal_case_insensitively(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"

    metadata = _metadata_for_file(raw_directory / "TJSP" / "page.json", raw_directory)

    assert metadata.alias == "api_publica_tjsp"
    assert metadata.sigla == "TJSP"


@pytest.mark.parametrize(
    ("relative_path", "error"),
    [
        ("page.json", "diretório de tribunal"),
        ("tjxx/page.json", "Tribunal sem mapeamento para tjxx"),
    ],
)
def test_metadata_for_file_rejects_unknown_layouts(
    tmp_path: Path,
    relative_path: str,
    error: str,
) -> None:
    raw_directory = tmp_path / "data" / "raw"

    with pytest.raises(BronzeProcessingError, match=error):
        _metadata_for_file(raw_directory / relative_path, raw_directory)


def test_metadata_for_file_rejects_files_outside_raw_directory(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"

    with pytest.raises(BronzeProcessingError, match="Arquivo fora de"):
        _metadata_for_file(tmp_path / "outro" / "tjsp" / "page.json", raw_directory)


def test_process_raw_file_keeps_only_included_processes(tmp_path: Path) -> None:
    raw_directory = tmp_path / "data" / "raw"
    file_path = raw_directory / "tjsp" / "response.json"
    _write_response(file_path, [{"id": "1234"}, {"id": "5678"}, {"id": "9999"}])
    session = FakeSession(["updated"])
    extracted_at = datetime(2026, 3, 2, 8, 0, tzinfo=UTC)

    result = process_raw_file(
        file_path,
        session,  # type: ignore[arg-type]
        raw_directory,
        included_datajud_ids={"5678"},
        extracted_at=extracted_at,
    )

    assert result.total == 1
    assert result.changed == 1
    assert len(session.statements) == 1
    parameters = session.statements[0].compile(dialect=postgresql.dialect()).params
    assert parameters["datajud_id"] == "5678"
    assert parameters["tribunal_sigla"] == "TJSP"
    assert parameters["extracted_at"] == extracted_at


def test_process_raw_file_without_selected_processes_changes_nothing(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"
    file_path = raw_directory / "tjsp" / "response.json"
    _write_response(file_path, [{"id": "1234"}])
    session = FakeSession([])

    result = process_raw_file(
        file_path,
        session,  # type: ignore[arg-type]
        raw_directory,
        included_datajud_ids=set(),
    )

    assert result == ProcessedFile(
        source_file="data/raw/tjsp/response.json", total=0, changed=0
    )
    assert session.statements == []


def test_process_raw_directory_processes_json_files_in_lexical_order(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"
    _write_response(raw_directory / "tjsp" / "b.json", [{"id": "2"}])
    _write_response(raw_directory / "tjsp" / "a.json", [{"id": "1"}])
    compressed = raw_directory / "tjsp" / "c.json.gz"
    with gzip.open(compressed, "wt", encoding="utf-8") as file:
        json.dump({"hits": {"hits": [{"_source": {"id": "3"}}]}}, file)
    (raw_directory / "tjsp" / "notas.txt").write_text("ignorado", encoding="utf-8")
    sessions: list[FakeSession] = []

    def session_factory() -> FakeSession:
        session = FakeSession(["inserted"])
        sessions.append(session)
        return session

    processed = process_raw_directory(
        raw_directory,
        session_factory,  # type: ignore[arg-type]
    )

    assert [item.source_file for item in processed] == [
        "data/raw/tjsp/a.json",
        "data/raw/tjsp/b.json",
        "data/raw/tjsp/c.json.gz",
    ]
    assert len(sessions) == 3
    assert all(item.changed == 1 for item in processed)


def test_process_raw_directory_stops_at_first_invalid_file(tmp_path: Path) -> None:
    raw_directory = tmp_path / "data" / "raw"
    _write_response(raw_directory / "tjsp" / "a.json", [{"movimentos": []}])
    _write_response(raw_directory / "tjsp" / "b.json", [{"id": "2"}])
    sessions: list[FakeSession] = []

    def session_factory() -> FakeSession:
        session = FakeSession(["inserted"])
        sessions.append(session)
        return session

    with pytest.raises(BronzeProcessingError, match="_source.id"):
        process_raw_directory(
            raw_directory,
            session_factory,  # type: ignore[arg-type]
        )

    assert len(sessions) == 1
    assert sessions[0].statements == []


def test_bronze_main_processes_files_and_syncs_silver(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session_factory = object()
    synced: list[object] = []

    def fake_sync(factory: object) -> SilverSyncReport:
        synced.append(factory)
        return SilverSyncReport(found=3, synced=3, movements=9, warnings=1)

    monkeypatch.setattr(
        bronze,
        "process_raw_directory",
        lambda: [
            ProcessedFile(source_file="a.json", total=2, changed=1),
            ProcessedFile(source_file="b.json", total=1, changed=1),
        ],
    )
    monkeypatch.setattr(bronze, "create_session_factory", lambda: session_factory)
    monkeypatch.setattr(bronze, "sync_bronze_to_silver", fake_sync)

    bronze.main()

    assert synced == [session_factory]
    output = capsys.readouterr().out
    assert "Bronze processada: 2 arquivo(s), 3 processo(s), 2 alteração(ões)." in output
    assert "Silver sincronizada: 3 processo(s), 9 movimento(s), 1 aviso(s)." in output


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
