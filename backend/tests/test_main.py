import logging
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest

from data_law import main as cli
from data_law.ingestion.ingestion import IngestionReport
from data_law.transformation.silver import SilverSyncReport

REPORT = IngestionReport(
    mode="incremental",
    run_started_at=datetime(2026, 3, 20, tzinfo=UTC),
    pages=2,
    candidates=10,
    persisted=4,
    changed=3,
    silver_synced=3,
    silver_movements=12,
    silver_warnings=1,
)


class FakeService:
    """Records how the CLI builds and runs the ingestion service."""

    instances: list["FakeService"] = []
    fail_with: Exception | None = None

    def __init__(
        self,
        client: Any,
        session_factory: Any,
        silver_sync: Any = None,
    ) -> None:
        self.client = client
        self.session_factory = session_factory
        self.silver_sync = silver_sync
        self.calls: list[str] = []
        FakeService.instances.append(self)

    def run_full(self) -> IngestionReport:
        return self._run("full")

    def run_incremental(self) -> IngestionReport:
        return self._run("incremental")

    def _run(self, mode: str) -> IngestionReport:
        self.calls.append(mode)
        if FakeService.fail_with is not None:
            raise FakeService.fail_with
        return replace(REPORT, mode=mode)


@pytest.fixture
def fake_cli(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    FakeService.instances = []
    FakeService.fail_with = None
    session_factory = object()
    synced: list[object] = []

    def fake_sync(factory: object) -> SilverSyncReport:
        synced.append(factory)
        return SilverSyncReport(found=0, synced=0, movements=0, warnings=0)

    monkeypatch.setattr(cli, "DataJudSettings", lambda: "settings")
    monkeypatch.setattr(cli, "DataJudClient", lambda settings: ("client", settings))
    monkeypatch.setattr(cli, "create_session_factory", lambda: session_factory)
    monkeypatch.setattr(cli, "DataJudIngestionService", FakeService)
    monkeypatch.setattr(cli, "sync_bronze_to_silver", fake_sync)
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    return {"session_factory": session_factory, "synced": synced}


def test_main_runs_incremental_ingestion_by_default(
    fake_cli: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli.main([])

    service = FakeService.instances[0]
    assert service.calls == ["incremental"]
    assert service.client == ("client", "settings")
    assert service.session_factory is fake_cli["session_factory"]
    output = capsys.readouterr().out
    assert "Ingestão incremental concluída: 2 página(s)" in output
    assert "10 candidato(s), 3 alteração(ões), 1 processo(s) sem alteração" in output
    assert "Silver: 3 processo(s), 12 movimento(s), 1 aviso(s)." in output


def test_main_runs_full_ingestion_with_flag(
    fake_cli: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli.main(["--full"])

    assert FakeService.instances[0].calls == ["full"]
    assert "Ingestão full concluída" in capsys.readouterr().out


def test_main_wires_silver_sync_to_the_same_session_factory(
    fake_cli: dict[str, Any],
) -> None:
    cli.main([])

    FakeService.instances[0].silver_sync()

    assert fake_cli["synced"] == [fake_cli["session_factory"]]


def test_main_logs_and_reraises_ingestion_errors(
    fake_cli: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    FakeService.fail_with = RuntimeError("DataJud fora do ar")

    with caplog.at_level(logging.ERROR, logger="data_law.main"):
        with pytest.raises(RuntimeError, match="DataJud fora do ar"):
            cli.main([])

    assert "Ingestão interrompida por erro" in caplog.text
    assert capsys.readouterr().out == ""


def test_configure_logging_uses_log_level_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: calls.append(kwargs))

    cli.configure_logging()

    assert calls[0]["level"] == "DEBUG"
