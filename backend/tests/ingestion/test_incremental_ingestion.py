import json
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
    DataJudIngestionError,
    DataJudIngestionService,
    InitialIngestionRequiredError,
    _RunProgress,
)
from data_law.ingestion.storage import save_raw_response as persist_raw_response
from data_law.transformation.silver import SilverSyncReport


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

    def save_raw(
        tribunal: str,
        payload: dict[str, Any],
        *,
        run_id: str,
        page: int,
        ingestion_date: str,
        raw_directory: Path,
    ) -> Path:
        return persist_raw_response(
            tribunal,
            payload,
            run_id=run_id,
            page=page,
            ingestion_date=ingestion_date,
            raw_directory=raw_directory,
        )

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
            page_size=100,
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
    assert len(client.bodies) == 1


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
    assert "Página Bronze concluída:" in caplog.text
    assert "Extração Bronze concluída" in caplog.text
    assert "Checkpoint salvo" in caplog.text
    assert "Ingestão concluída:" in caplog.text


def test_service_rejects_unknown_tribunal() -> None:
    with pytest.raises(ValueError, match="Tribunal não configurado: tjxx"):
        DataJudIngestionService(
            FakeClient([]),  # type: ignore[arg-type]
            lambda: FakeSession(),  # type: ignore[arg-type,return-value]
            tribunal_key="tjxx",
        )


@pytest.mark.parametrize("page_size", [0, -1])
def test_service_rejects_non_positive_page_size(page_size: int) -> None:
    with pytest.raises(ValueError, match="page_size"):
        DataJudIngestionService(
            FakeClient([]),  # type: ignore[arg-type]
            lambda: FakeSession(),  # type: ignore[arg-type,return-value]
            page_size=page_size,
        )


def test_page_without_selected_processes_is_saved_but_not_persisted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    unfinished = _source(
        "unfinished",
        [{"codigo": 970, "dataHora": (now - timedelta(days=1)).isoformat()}],
        timestamp=now,
    )
    client = FakeClient([_response(unfinished)])
    session = FakeSession()
    service, calls = _service(monkeypatch, tmp_path, client, session)

    report = service.run_full()

    assert report.pages == 1
    assert report.candidates == 1
    assert report.persisted == 0
    assert report.changed == 0
    assert calls == []
    assert session.state is not None


def test_full_load_runs_silver_sync_and_reports_its_totals(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    source = _source(
        "completed",
        [{"codigo": 246, "dataHora": (now - timedelta(days=1)).isoformat()}],
        timestamp=now,
    )
    service, _ = _service(
        monkeypatch, tmp_path, FakeClient([_response(source)]), FakeSession()
    )
    service.silver_sync = lambda: SilverSyncReport(
        found=1, synced=1, movements=4, warnings=2
    )

    report = service.run_full()

    assert report.silver_synced == 1
    assert report.silver_movements == 4
    assert report.silver_warnings == 2


def test_full_load_stops_when_datajud_times_out(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session = FakeSession()
    service, _ = _service(
        monkeypatch,
        tmp_path,
        FakeClient([{"timed_out": True, "hits": {"hits": []}}]),
        session,
    )

    with pytest.raises(DataJudIngestionError, match="tempo limite"):
        service.run_full()

    assert session.state is None


def test_full_page_without_sort_cursor_stops_pagination(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    response = _response(
        *[_source(str(index), [], timestamp=now) for index in range(100)]
    )
    del response["hits"]["hits"][-1]["sort"]
    session = FakeSession()
    service, _ = _service(monkeypatch, tmp_path, FakeClient([response]), session)

    with pytest.raises(DataJudIngestionError, match="cursor de paginação"):
        service.run_full()

    assert session.state is None


def test_incremental_load_keeps_naive_checkpoint_as_utc(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    checkpoint = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    state = BronzeDataJudIngestionState(
        tribunal_alias="api_publica_tjsp",
        tribunal_sigla="TJSP",
        last_successful_at=checkpoint,
    )
    client = FakeClient([_response()])
    service, _ = _service(monkeypatch, tmp_path, client, FakeSession(state))

    service.run_incremental()

    date_filter = client.bodies[0]["query"]["bool"]["filter"][1]["range"]
    expected_start = checkpoint.replace(tzinfo=UTC) - service.incremental_overlap
    assert date_filter["@timestamp"]["gte"] == (
        expected_start.isoformat().replace("+00:00", "Z")
    )


def test_monthly_windows_use_distinct_raw_page_numbers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    march_start = datetime(2026, 3, 1, tzinfo=UTC)
    april_start = datetime(2026, 4, 1, tzinfo=UTC)
    may_start = datetime(2026, 5, 1, tzinfo=UTC)
    march_source = _source(
        "march",
        [{"codigo": 22, "dataHora": datetime(2026, 3, 15, tzinfo=UTC).isoformat()}],
        timestamp=datetime(2026, 3, 15, tzinfo=UTC),
    )
    april_source = _source(
        "april",
        [{"codigo": 22, "dataHora": datetime(2026, 4, 15, tzinfo=UTC).isoformat()}],
        timestamp=datetime(2026, 4, 15, tzinfo=UTC),
    )
    client = FakeClient([_response(march_source), _response(april_source)])
    service, calls = _service(monkeypatch, tmp_path, client, FakeSession())
    progress = _RunProgress(
        run_id="20260501T000000Z-12345678",
        tribunal_key="tjsp",
        mode="full",
        tribunal="TJSP",
        run_started_at=may_start,
        query_start=march_start,
        query_end=may_start,
        completion_window_start=march_start,
        strategy="monthly",
        windows=[
            (march_start, april_start, True),
            (april_start, may_start, False),
        ],
        page_size=100,
    )

    report = service._run(progress)

    run_directory = (
        tmp_path
        / "data/raw/tjsp/ingestion_date=2026-05-01"
        / f"run_id={progress.run_id}"
    )
    raw_files = sorted(run_directory.glob("page-*.json.gz"))
    assert report.pages == 2
    assert calls == [{"march"}, {"april"}]
    assert [path.name for path in raw_files] == [
        "page-000001.json.gz",
        "page-000002.json.gz",
    ]
    assert len(client.bodies) == 2


def test_resume_reprocesses_saved_raw_page_without_a_new_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    source = _source(
        "completed",
        [{"codigo": 22, "dataHora": (now - timedelta(days=1)).isoformat()}],
        timestamp=now,
    )
    client = FakeClient([_response(source)])
    service, calls = _service(monkeypatch, tmp_path, client, FakeSession())

    def fail_processing(*args: object, **kwargs: object) -> ProcessedFile:
        raise RuntimeError("interrupção simulada")

    monkeypatch.setattr(
        "data_law.ingestion.ingestion.process_raw_file", fail_processing
    )
    with pytest.raises(RuntimeError, match="interrupção simulada"):
        service.run_full()

    state_path = next((tmp_path / "data/raw/tjsp").glob("**/.progress.state"))
    run_id = json.loads(state_path.read_text(encoding="utf-8"))["run_id"]
    requests_before_resume = len(client.bodies)

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

    monkeypatch.setattr("data_law.ingestion.ingestion.process_raw_file", process_raw)
    report = service.resume_run(run_id)

    assert report.persisted == 1
    assert calls == [{"completed"}]
    assert len(client.bodies) == requests_before_resume
