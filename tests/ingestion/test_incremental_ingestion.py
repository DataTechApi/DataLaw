from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from data_law.infra.database.model.bronze.ingestion_state import (
    BronzeDataJudIngestionState,
)
from data_law.ingestion.bronze import ProcessedFile
from data_law.ingestion.ingestion import (
    DataJudIngestionService,
    InitialIngestionRequiredError,
)


class FakeClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.bodies: list[dict[str, Any]] = []

    def ingest(self, tribunal: str, body: dict[str, Any]) -> dict[str, Any]:
        assert tribunal == "api_publica_tjsp"
        self.bodies.append(body)
        return self.responses.pop(0)


class FakeSession:
    def __init__(
        self,
        state: BronzeDataJudIngestionState | None = None,
        existing_ids: set[str] | None = None,
    ) -> None:
        self.state = state
        self.existing_ids = existing_ids or set()

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, model: type[object], key: str) -> BronzeDataJudIngestionState | None:
        assert model is BronzeDataJudIngestionState
        assert key == "api_publica_tjsp"
        return self.state

    def scalars(self, statement: object) -> set[str]:
        return self.existing_ids

    @contextmanager
    def begin(self):
        yield self

    def add(self, state: BronzeDataJudIngestionState) -> None:
        self.state = state


def _hit(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "_source": source,
        "sort": [source["@timestamp"], source["id"]],
    }


def _response(*sources: dict[str, Any]) -> dict[str, Any]:
    return {"timed_out": False, "hits": {"hits": [_hit(source) for source in sources]}}


def _source(
    datajud_id: str,
    movements: list[dict[str, Any]],
    *,
    timestamp: datetime,
) -> dict[str, Any]:
    return {
        "id": datajud_id,
        "@timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "movimentos": movements,
    }


def _service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    client: FakeClient,
    session: FakeSession,
) -> tuple[DataJudIngestionService, list[set[str]]]:
    calls: list[set[str]] = []

    def save_raw(*args: object, **kwargs: object) -> Path:
        return tmp_path / "data" / "raw" / "tjsp" / "page.json.gz"

    def process_raw(
        file_path: Path,
        database_session: FakeSession,
        **kwargs: object,
    ) -> ProcessedFile:
        included = kwargs["included_datajud_ids"]
        assert isinstance(included, set)
        calls.append(included)
        return ProcessedFile(
            source_file=str(file_path), total=len(included), changed=len(included)
        )

    monkeypatch.setattr("data_law.ingestion.ingestion.save_raw_response", save_raw)
    monkeypatch.setattr("data_law.ingestion.ingestion.process_raw_file", process_raw)
    return (
        DataJudIngestionService(
            client,  # type: ignore[arg-type]
            lambda: session,  # type: ignore[arg-type]
            raw_directory=tmp_path / "data" / "raw",
            page_size=2,
        ),
        calls,
    )


def test_full_load_persists_only_completion_in_the_same_movement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    exact = _source(
        "exact",
        [{"codigo": 22, "dataHora": (now - timedelta(days=1)).isoformat()}],
        timestamp=now,
    )
    false_positive = _source(
        "false-positive",
        [
            {"codigo": 246, "dataHora": (now - timedelta(days=365)).isoformat()},
            {"codigo": 970, "dataHora": (now - timedelta(days=1)).isoformat()},
        ],
        timestamp=now,
    )
    client = FakeClient([_response(exact, false_positive), _response()])
    session = FakeSession()
    service, calls = _service(monkeypatch, tmp_path, client, session)

    report = service.run_full()

    assert report.mode == "full"
    assert report.candidates == 2
    assert report.persisted == 1
    assert calls == [{"exact"}]
    assert session.state is not None
    date_filter = client.bodies[0]["query"]["bool"]["filter"][1]["range"]
    assert "movimentos.dataHora" in date_filter
    assert date_filter["movimentos.dataHora"]["gte"] == "2026-03-01T00:00:00Z"
    assert "search_after" in client.bodies[1]


def test_incremental_load_updates_known_process_and_new_completion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    checkpoint = now - timedelta(days=3)
    state = BronzeDataJudIngestionState(
        tribunal_alias="api_publica_tjsp",
        tribunal_sigla="TJSP",
        last_successful_at=checkpoint,
    )
    known = _source(
        "known",
        [
            {"codigo": 22, "dataHora": (now - timedelta(days=365)).isoformat()},
            {"codigo": 970, "dataHora": (now - timedelta(hours=1)).isoformat()},
        ],
        timestamp=now,
    )
    new_completion = _source(
        "new",
        [{"codigo": 246, "dataHora": (now - timedelta(hours=1)).isoformat()}],
        timestamp=now,
    )
    client = FakeClient([_response(known, new_completion), _response()])
    session = FakeSession(state, existing_ids={"known"})
    service, calls = _service(monkeypatch, tmp_path, client, session)

    report = service.run_incremental()

    assert report.mode == "incremental"
    assert calls == [{"known", "new"}]
    date_filter = client.bodies[0]["query"]["bool"]["filter"][1]["range"]
    assert "@timestamp" in date_filter
    assert session.state is not None
    assert session.state.last_successful_at > checkpoint


def test_incremental_load_requires_a_completed_historical_load(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, _ = _service(monkeypatch, tmp_path, FakeClient([]), FakeSession())

    with pytest.raises(InitialIngestionRequiredError, match="full-ingest"):
        service.run_incremental()


def test_full_load_logs_progress_and_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    now = datetime.now(UTC)
    source = _source(
        "completed",
        [{"codigo": 22, "dataHora": (now - timedelta(days=1)).isoformat()}],
        timestamp=now,
    )
    service, _ = _service(
        monkeypatch,
        tmp_path,
        FakeClient([_response(source)]),
        FakeSession(),
    )

    with caplog.at_level("INFO", logger="data_law.ingestion.ingestion"):
        service.run_full()

    assert "Iniciando ingestão histórica" in caplog.text
    assert "Página processada: página=1 candidatos=1 selecionados=1" in caplog.text
    assert "Ingestão Bronze concluída" in caplog.text
    assert "Checkpoint salvo" in caplog.text
    assert "Ingestão concluída:" in caplog.text
