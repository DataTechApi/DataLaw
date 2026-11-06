import calendar
import gzip
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
)

from data_law.infra.database.model.bronze.bronze_process import (
    BronzeDataJudExtract,
)
from data_law.infra.database.model.bronze.ingestion_state import (
    BronzeDataJudIngestionState,
)
from data_law.infra.database.session import SessionFactory
from data_law.ingestion.bronze import RAW_DIRECTORY, TRIBUNAL_METADATA, process_raw_file
from data_law.ingestion.storage import save_raw_response
from data_law.transformation.silver import SilverSyncReport

COMPLETION_CODES = frozenset({22, 246})
PAGE_SIZE = 500
MIN_PAGE_SIZE = 100
_PAGE_SIZE_FALLBACKS = (250, 100)
INCREMENTAL_OVERLAP = timedelta(hours=48)
HISTORICAL_START = datetime(2026, 3, 1, tzinfo=UTC)
PROGRESS_FILENAME = ".progress.state"
BACKEND_DIRECTORY = Path(__file__).resolve().parents[3]

logger = logging.getLogger(__name__)


class DataJudSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(validation_alias="DATAJUD_API_KEY")
    url: str = "https://api-publica.datajud.cnj.jus.br"


def _is_retryable_request_error(error: BaseException) -> bool:
    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        return response is not None and response.status_code in {
            408,
            429,
            500,
            502,
            503,
            504,
        }
    return isinstance(
        error,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ),
    )


def _datajud_retry_wait(retry_state: Any) -> float:
    error = retry_state.outcome.exception()
    response = getattr(error, "response", None)
    retry_after = response.headers.get("Retry-After") if response is not None else None
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=UTC)
                return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
    return float(min(4 * (2 ** (retry_state.attempt_number - 1)), 30))


class DataJudClient:
    def __init__(self, settings: DataJudSettings) -> None:
        self.url = settings.url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"APIKey {settings.api_key.get_secret_value()}"}
        )

    def close(self) -> None:
        self.session.close()

    # Retry up to five times with exponential backoff.
    @retry(
        wait=_datajud_retry_wait,
        stop=stop_after_attempt(3),
        retry=retry_if_exception(_is_retryable_request_error),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def ingest(self, tribunal: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{self.url}/{tribunal}/_search",
            json=body,
            # DataJud calls can be slow.
            timeout=90,
        )
        response.raise_for_status()
        return response.json()


class InitialIngestionRequiredError(RuntimeError):
    """Raised when an incremental run is attempted before a historical load."""


class DataJudIngestionError(RuntimeError):
    """Raised when a DataJud response cannot be paginated or classified safely."""


@dataclass(frozen=True)
class IngestionReport:
    mode: str
    run_started_at: datetime
    pages: int
    candidates: int
    persisted: int
    changed: int
    silver_synced: int = 0
    silver_movements: int = 0
    silver_warnings: int = 0

    @property
    def unchanged(self) -> int:
        return self.persisted - self.changed


@dataclass
class _RunProgress:
    run_id: str
    tribunal_key: str
    mode: str
    run_started_at: datetime
    query_start: datetime
    query_end: datetime
    completion_window_start: datetime
    strategy: str
    windows: list[tuple[datetime, datetime, bool]]
    window_index: int = 0
    search_after: list[Any] | None = None
    page_size: int = PAGE_SIZE
    next_page: int = 1
    pages: int = 0
    candidates: int = 0
    persisted: int = 0
    changed: int = 0
    phase: str = "extract"
    tribunal: str = ""


def _new_run_id(started_at: datetime) -> str:
    return f"{started_at.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def _serialize_progress(progress: _RunProgress) -> dict[str, object]:
    return {
        "run_id": progress.run_id,
        "tribunal_key": progress.tribunal_key,
        "tribunal": progress.tribunal,
        "mode": progress.mode,
        "run_started_at": progress.run_started_at.isoformat(),
        "query_start": progress.query_start.isoformat(),
        "query_end": progress.query_end.isoformat(),
        "completion_window_start": progress.completion_window_start.isoformat(),
        "strategy": progress.strategy,
        "windows": [
            [start.isoformat(), end.isoformat(), exclusive]
            for start, end, exclusive in progress.windows
        ],
        "window_index": progress.window_index,
        "search_after": progress.search_after,
        "page_size": progress.page_size,
        "next_page": progress.next_page,
        "pages": progress.pages,
        "candidates": progress.candidates,
        "persisted": progress.persisted,
        "changed": progress.changed,
        "phase": progress.phase,
    }


def _load_progress(path: Path) -> _RunProgress:
    try:
        with path.open(encoding="utf-8") as file:
            raw = json.load(file)
        if not isinstance(raw, dict):
            raise TypeError("documento JSON não é um objeto")
        raw_windows = raw["windows"]
        if not isinstance(raw_windows, list):
            raise TypeError("windows não é uma lista")
        windows = []
        for window in raw_windows:
            if (
                not isinstance(window, list)
                or len(window) != 3
                or not isinstance(window[0], str)
                or not isinstance(window[1], str)
                or not isinstance(window[2], bool)
            ):
                raise TypeError("janela inválida")
            windows.append(
                (
                    datetime.fromisoformat(window[0]),
                    datetime.fromisoformat(window[1]),
                    window[2],
                )
            )
        progress = _RunProgress(
            run_id=str(raw["run_id"]),
            tribunal_key=str(raw["tribunal_key"]),
            mode=str(raw["mode"]),
            run_started_at=datetime.fromisoformat(str(raw["run_started_at"])),
            query_start=datetime.fromisoformat(str(raw["query_start"])),
            query_end=datetime.fromisoformat(str(raw["query_end"])),
            completion_window_start=datetime.fromisoformat(
                str(raw["completion_window_start"])
            ),
            strategy=str(raw.get("strategy", "single")),
            windows=windows,
            window_index=int(raw.get("window_index", 0)),
            search_after=raw.get("search_after"),
            page_size=int(raw["page_size"]),
            next_page=int(raw.get("next_page", 1)),
            pages=int(raw.get("pages", 0)),
            candidates=int(raw.get("candidates", 0)),
            persisted=int(raw.get("persisted", 0)),
            changed=int(raw.get("changed", 0)),
            phase=str(raw.get("phase", "extract")),
            tribunal=str(raw["tribunal"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"Estado de retomada inválido em {path}") from error

    if progress.mode not in {"full", "incremental"}:
        raise ValueError(f"Modo de retomada inválido em {path}")
    if progress.phase not in {"extract", "silver", "complete"}:
        raise ValueError(f"Etapa de retomada inválida em {path}")
    if progress.strategy not in {"single", "monthly"}:
        raise ValueError(f"Estratégia de retomada inválida em {path}")
    if not MIN_PAGE_SIZE <= progress.page_size <= 10_000:
        raise ValueError(f"Tamanho de página inválido em {path}")
    if (
        progress.next_page < 1
        or min(
            progress.pages,
            progress.candidates,
            progress.persisted,
            progress.changed,
        )
        < 0
    ):
        raise ValueError(f"Contadores de retomada inválidos em {path}")
    if progress.phase == "extract" and (
        not progress.windows or not 0 <= progress.window_index < len(progress.windows)
    ):
        raise ValueError(f"Janela de retomada inválida em {path}")
    return progress


def _read_raw_response(path: Path) -> dict[str, object]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as file:
        document = json.load(file)
    if not isinstance(document, dict):
        raise DataJudIngestionError(f"Resposta Raw inválida: {path}")
    return document


def _smaller_page_size(current: int) -> int | None:
    for candidate in _PAGE_SIZE_FALLBACKS:
        if candidate < current:
            return candidate
    if current > MIN_PAGE_SIZE:
        return MIN_PAGE_SIZE
    return None


def _monthly_windows(
    start: datetime, end: datetime
) -> list[tuple[datetime, datetime, bool]]:
    windows: list[tuple[datetime, datetime, bool]] = []
    cursor = start
    while cursor < end:
        if cursor.month == 12:
            next_month = cursor.replace(
                year=cursor.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month = cursor.replace(
                month=cursor.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        boundary = min(next_month, end)
        windows.append((cursor, boundary, boundary < end))
        cursor = boundary
    if not windows:
        windows.append((start, end, False))
    return windows


class DataJudIngestionService:
    """Run the historical and incremental DataJud ingestion flows for one tribunal."""

    def __init__(
        self,
        client: DataJudClient,
        session_factory: SessionFactory,
        silver_sync: Callable[[], SilverSyncReport] | None = None,
        *,
        tribunal_key: str = "tjsp",
        raw_directory: Path = RAW_DIRECTORY,
        page_size: int = PAGE_SIZE,
        incremental_overlap: timedelta = INCREMENTAL_OVERLAP,
    ) -> None:
        try:
            metadata = TRIBUNAL_METADATA[tribunal_key]
        except KeyError as error:
            raise ValueError(f"Tribunal não configurado: {tribunal_key}") from error

        if not MIN_PAGE_SIZE <= page_size <= 10_000:
            raise ValueError("page_size deve estar entre 100 e 10000")

        self.client = client
        self.session_factory = session_factory
        self.silver_sync = silver_sync
        self.tribunal_key = tribunal_key
        self.metadata = metadata
        self.raw_directory = raw_directory
        self.page_size = page_size
        self.incremental_overlap = incremental_overlap

    def run_full(self) -> IngestionReport:
        """Backfill processes with a completion movement since March 2026."""
        run_started_at = datetime.now(UTC)
        logger.info(
            "Iniciando ingestão histórica: tribunal=%s janela=%s até=%s",
            self.metadata.sigla,
            _format_timestamp(HISTORICAL_START),
            _format_timestamp(run_started_at),
        )
        progress = _RunProgress(
            run_id=_new_run_id(run_started_at),
            tribunal_key=self.tribunal_key,
            mode="full",
            run_started_at=run_started_at,
            query_start=HISTORICAL_START,
            query_end=run_started_at,
            completion_window_start=HISTORICAL_START,
            strategy="single",
            windows=[(HISTORICAL_START, run_started_at, False)],
            page_size=self.page_size,
        )
        self._save_progress(progress)
        return self._run(progress)

    def run_incremental(self) -> IngestionReport:
        """Refresh newly finalized processes and updates to known completed ones."""
        checkpoint = self._checkpoint()
        if checkpoint is None:
            raise InitialIngestionRequiredError(
                "Carga histórica ausente para "
                f"{self.metadata.sigla}. Execute `uv run python -m data_law.main "
                f"--tribunal {self.tribunal_key} --full` (full-ingest) primeiro."
            )

        run_started_at = datetime.now(UTC)
        window_start = _subtract_calendar_months(run_started_at, 6)
        logger.info(
            "Iniciando ingestão incremental: tribunal=%s checkpoint=%s sobreposição=%s",
            self.metadata.sigla,
            _format_timestamp(checkpoint),
            self.incremental_overlap,
        )
        progress = _RunProgress(
            run_id=_new_run_id(run_started_at),
            tribunal_key=self.tribunal_key,
            mode="incremental",
            run_started_at=run_started_at,
            query_start=checkpoint - self.incremental_overlap,
            query_end=run_started_at,
            completion_window_start=window_start,
            strategy="single",
            windows=[(checkpoint - self.incremental_overlap, run_started_at, False)],
            page_size=self.page_size,
        )
        self._save_progress(progress)
        return self._run(progress)

    def resume_run(self, run_id: str) -> IngestionReport:
        """Resume an interrupted run from its local progress state."""
        if not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", run_id):
            raise ValueError(f"run_id inválido: {run_id}")
        tribunal_directory = self.raw_directory / self.tribunal_key
        matching_paths = list(
            tribunal_directory.glob(
                f"ingestion_date=*/run_id={run_id}/{PROGRESS_FILENAME}"
            )
        )
        if len(matching_paths) != 1:
            raise ValueError(
                "Execução incompleta não encontrada para "
                f"{self.metadata.sigla}: {run_id}"
            )
        progress = _load_progress(matching_paths[0])
        if progress.tribunal_key != self.tribunal_key:
            raise ValueError("O tribunal informado não corresponde à execução")
        if progress.phase == "complete":
            raise ValueError(f"A execução {run_id} já foi concluída")
        logger.info(
            "Retomando execução: id=%s modo=%s fase=%s tribunal=%s",
            progress.run_id,
            progress.mode,
            progress.phase,
            self.metadata.sigla,
        )
        return self._run(progress)

    def _run(self, progress: _RunProgress) -> IngestionReport:
        logger.info(
            "Execução de ingestão iniciada: id=%s modo=%s tribunal=%s estratégia=%s",
            progress.run_id,
            progress.mode,
            self.metadata.sigla,
            progress.strategy,
        )
        while progress.phase == "extract":
            window_start, window_end, end_exclusive = progress.windows[
                progress.window_index
            ]
            query = (
                _historical_query(
                    window_start,
                    window_end,
                    end_exclusive=end_exclusive,
                )
                if progress.mode == "full"
                else _incremental_query(window_start, window_end)
            )
            page_path = self._raw_page_path(progress, progress.next_page)

            if page_path.exists():
                response = _read_raw_response(page_path)
                logger.info(
                    "Reprocessando página Raw pendente: run_id=%s página=%s arquivo=%s",
                    progress.run_id,
                    progress.next_page,
                    page_path,
                )
            else:
                body = _search_body(
                    query,
                    page_size=progress.page_size,
                    search_after=progress.search_after,
                )
                started = datetime.now(UTC)
                try:
                    response = self.client.ingest(self.metadata.alias, body)
                except requests.exceptions.RequestException as error:
                    if not _is_retryable_request_error(error):
                        raise
                    next_size = _smaller_page_size(progress.page_size)
                    if next_size is not None:
                        logger.warning(
                            "Reduzindo página após falhas temporárias: tribunal=%s "
                            "página=%s tamanho=%s novo_tamanho=%s",
                            self.metadata.sigla,
                            progress.next_page,
                            progress.page_size,
                            next_size,
                        )
                        progress.page_size = next_size
                        self._save_progress(progress)
                        continue
                    if progress.mode == "full" and progress.strategy == "single":
                        logger.warning(
                            "Consulta histórica ainda falha com página mínima; "
                            "alternando para janelas mensais: tribunal=%s",
                            self.metadata.sigla,
                        )
                        progress.strategy = "monthly"
                        progress.windows = _monthly_windows(
                            progress.query_start,
                            progress.query_end,
                        )
                        progress.window_index = 0
                        progress.search_after = None
                        progress.page_size = self.page_size
                        self._save_progress(progress)
                        continue
                    raise

                elapsed = (datetime.now(UTC) - started).total_seconds()
                hits = _response_hits(response)
                if hits:
                    page_path = save_raw_response(
                        self.tribunal_key,
                        response,
                        run_id=progress.run_id,
                        page=progress.next_page,
                        ingestion_date=progress.run_started_at.date().isoformat(),
                        raw_directory=self.raw_directory,
                    )
                logger.info(
                    "Resposta DataJud: run_id=%s janela=%s/%s página=%s "
                    "tamanho=%s hits=%s duração=%.2fs",
                    progress.run_id,
                    progress.window_index + 1,
                    len(progress.windows),
                    progress.next_page,
                    progress.page_size,
                    len(hits),
                    elapsed,
                )

            hits = _response_hits(response)
            if not hits:
                logger.info(
                    "Janela sem resultados adicionais: run_id=%s janela=%s/%s",
                    progress.run_id,
                    progress.window_index + 1,
                    len(progress.windows),
                )
                self._advance_window(progress)
                self._save_progress(progress)
                continue

            sources = _source_payloads(hits)
            source_ids = {source["id"] for source in sources}
            existing_ids = (
                self._existing_datajud_ids(source_ids)
                if progress.mode == "incremental"
                else set()
            )
            included_ids = {
                source["id"]
                for source in sources
                if _has_completion_in_window(
                    source,
                    start=(
                        progress.completion_window_start
                        if progress.mode == "incremental"
                        else window_start
                    ),
                    end=(
                        progress.run_started_at
                        if progress.mode == "incremental"
                        else window_end
                    ),
                    end_exclusive=(
                        False if progress.mode == "incremental" else end_exclusive
                    ),
                )
                or source["id"] in existing_ids
            }

            persisted = changed = 0
            if included_ids:
                with self.session_factory() as session:
                    result = process_raw_file(
                        page_path,
                        session,
                        raw_directory=self.raw_directory,
                        included_datajud_ids=included_ids,
                        extracted_at=progress.run_started_at,
                    )
                persisted = result.total
                changed = result.changed

            progress.pages += 1
            progress.candidates += len(sources)
            progress.persisted += persisted
            progress.changed += changed
            logger.info(
                "Página Bronze concluída: run_id=%s janela=%s/%s página=%s "
                "candidatos=%s selecionados=%s persistidos=%s alterados=%s",
                progress.run_id,
                progress.window_index + 1,
                len(progress.windows),
                progress.next_page,
                len(sources),
                len(included_ids),
                persisted,
                changed,
            )

            progress.next_page += 1
            if len(hits) < progress.page_size:
                self._advance_window(progress)
            else:
                progress.search_after = _last_sort_value(hits[-1])
            self._save_progress(progress)

        if progress.phase == "silver":
            return self._finish_silver(progress)
        raise RuntimeError(f"Etapa de execução desconhecida: {progress.phase}")

    def _advance_window(self, progress: _RunProgress) -> None:
        progress.window_index += 1
        progress.search_after = None
        progress.page_size = self.page_size
        if progress.window_index >= len(progress.windows):
            progress.phase = "silver"
            logger.info(
                "Extração Bronze concluída: páginas=%s candidatos=%s persistidos=%s "
                "alterados=%s",
                progress.pages,
                progress.candidates,
                progress.persisted,
                progress.changed,
            )

    def _finish_silver(self, progress: _RunProgress) -> IngestionReport:
        self._save_progress(progress)
        logger.info("Iniciando sincronização Silver: tribunal=%s", self.metadata.sigla)
        silver_report = self.silver_sync() if self.silver_sync is not None else None
        if silver_report is not None:
            logger.info(
                "Sincronização Silver concluída: processos=%s movimentos=%s avisos=%s",
                silver_report.synced,
                silver_report.movements,
                silver_report.warnings,
            )
        self._save_checkpoint(progress.run_started_at)
        progress.phase = "complete"
        self._save_progress(progress)
        logger.info(
            "Checkpoint salvo: concluído_em=%s",
            _format_timestamp(progress.run_started_at),
        )
        report = IngestionReport(
            mode=progress.mode,
            run_started_at=progress.run_started_at,
            pages=progress.pages,
            candidates=progress.candidates,
            persisted=progress.persisted,
            changed=progress.changed,
            silver_synced=silver_report.synced if silver_report is not None else 0,
            silver_movements=silver_report.movements
            if silver_report is not None
            else 0,
            silver_warnings=silver_report.warnings if silver_report is not None else 0,
        )
        logger.info(
            "Ingestão concluída: id=%s modo=%s páginas=%s candidatos=%s "
            "alterados=%s sem_alteração=%s",
            progress.run_id,
            report.mode,
            report.pages,
            report.candidates,
            report.changed,
            report.unchanged,
        )
        return report

    def _raw_page_path(self, progress: _RunProgress, page: int) -> Path:
        return (
            self.raw_directory
            / self.tribunal_key
            / f"ingestion_date={progress.run_started_at.date().isoformat()}"
            / f"run_id={progress.run_id}"
            / f"page-{page:06d}.json.gz"
        )

    def _progress_path(self, progress: _RunProgress) -> Path:
        return self._raw_page_path(progress, 1).parent / PROGRESS_FILENAME

    def _save_progress(self, progress: _RunProgress) -> None:
        if not getattr(progress, "tribunal", None):
            progress.tribunal = self.metadata.sigla
        path = self._progress_path(progress)
        path.parent.mkdir(parents=True, exist_ok=True)
        document = _serialize_progress(progress)
        temporary_path = path.with_name(f"{path.name}.part")
        try:
            temporary_path.write_text(
                json.dumps(document, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            temporary_path.replace(path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def _checkpoint(self) -> datetime | None:
        with self.session_factory() as session:
            state = session.get(
                BronzeDataJudIngestionState,
                self.metadata.alias,
            )
        if state is None:
            return None
        return _as_utc(state.last_successful_at)

    def _existing_datajud_ids(self, datajud_ids: set[str]) -> set[str]:
        if not datajud_ids:
            return set()

        with self.session_factory() as session:
            rows = session.scalars(
                select(BronzeDataJudExtract.datajud_id).where(
                    BronzeDataJudExtract.tribunal_sigla == self.metadata.sigla,
                    BronzeDataJudExtract.datajud_id.in_(datajud_ids),
                )
            )
            return set(rows)

    def _save_checkpoint(self, completed_at: datetime) -> None:
        with self.session_factory() as session:
            with session.begin():
                state = session.get(
                    BronzeDataJudIngestionState,
                    self.metadata.alias,
                )
                if state is None:
                    session.add(
                        BronzeDataJudIngestionState(
                            tribunal_alias=self.metadata.alias,
                            tribunal_sigla=self.metadata.sigla,
                            last_successful_at=completed_at,
                        )
                    )
                else:
                    state.tribunal_sigla = self.metadata.sigla
                    state.last_successful_at = completed_at


def _historical_query(
    start: datetime,
    end: datetime,
    *,
    end_exclusive: bool = False,
) -> dict[str, Any]:
    return {
        "bool": {
            "filter": [
                {"terms": {"movimentos.codigo": sorted(COMPLETION_CODES)}},
                {
                    "range": {
                        "movimentos.dataHora": {
                            "gte": _format_timestamp(start),
                            "lt" if end_exclusive else "lte": _format_timestamp(end),
                        }
                    }
                },
            ]
        }
    }


def _incremental_query(start: datetime, end: datetime) -> dict[str, Any]:
    return {
        "bool": {
            "filter": [
                {"terms": {"movimentos.codigo": sorted(COMPLETION_CODES)}},
                {
                    "range": {
                        "@timestamp": {
                            "gte": _format_timestamp(start),
                            "lte": _format_timestamp(end),
                        }
                    }
                },
            ]
        }
    }


def _search_body(
    query: dict[str, Any],
    *,
    page_size: int,
    search_after: list[Any] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "size": page_size,
        "track_total_hits": False,
        "query": query,
        "sort": [
            {"@timestamp": {"order": "asc"}},
            {"id.keyword": {"order": "asc"}},
        ],
    }
    if search_after is not None:
        body["search_after"] = search_after
    return body


def _response_hits(response: dict[str, Any]) -> list[dict[str, Any]]:
    if response.get("timed_out") is True:
        raise DataJudIngestionError("A consulta DataJud excedeu o tempo limite")

    hits = response.get("hits")
    hit_list = hits.get("hits") if isinstance(hits, dict) else None
    if not isinstance(hit_list, list) or not all(
        isinstance(hit, dict) for hit in hit_list
    ):
        raise DataJudIngestionError("Resposta DataJud sem hits.hits válido")
    return hit_list


def _source_payloads(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for position, hit in enumerate(hits):
        source = hit.get("_source")
        if not isinstance(source, dict):
            raise DataJudIngestionError(f"Hit {position} da API sem _source válido")
        datajud_id = source.get("id")
        if not isinstance(datajud_id, str) or not datajud_id.strip():
            raise DataJudIngestionError(f"Hit {position} da API sem _source.id válido")
        sources.append(source)
    return sources


def _last_sort_value(hit: dict[str, Any]) -> list[Any]:
    sort_value = hit.get("sort")
    if not isinstance(sort_value, list) or len(sort_value) != 2:
        raise DataJudIngestionError(
            "Resposta DataJud sem o cursor de paginação esperado"
        )
    return sort_value


def _has_completion_in_window(
    process: dict[str, Any],
    *,
    start: datetime,
    end: datetime,
    end_exclusive: bool = False,
) -> bool:
    movements = process.get("movimentos")
    if not isinstance(movements, list):
        return False

    for movement in movements:
        if not isinstance(movement, dict):
            continue
        if movement.get("codigo") not in COMPLETION_CODES:
            continue
        value = movement.get("dataHora")
        if not isinstance(value, str):
            continue
        try:
            occurred_at = _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            continue
        if start <= occurred_at < end if end_exclusive else start <= occurred_at <= end:
            return True
    return False


def _subtract_calendar_months(value: datetime, months: int) -> datetime:
    month_index = value.year * 12 + value.month - 1 - months
    year, month_offset = divmod(month_index, 12)
    month = month_offset + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
