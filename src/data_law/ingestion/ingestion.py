import calendar
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
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

COMPLETION_CODES = frozenset({22, 246})
PAGE_SIZE = 500
INCREMENTAL_OVERLAP = timedelta(hours=48)


class DataJudSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(validation_alias="DATAJUD_API_KEY")
    url: str = "https://api-publica.datajud.cnj.jus.br"


class DataJudClient:
    def __init__(self, settings: DataJudSettings) -> None:
        self.url = settings.url.rstrip("/")
        self.headers = {
            "Authorization": f"APIKey {settings.api_key.get_secret_value()}"
        }

    # Retry up to five times with exponential backoff.
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=15),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True,
    )
    def ingest(self, tribunal: str, body: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.url}/{tribunal}/_search",
            json=body,
            headers=self.headers,
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

    @property
    def unchanged(self) -> int:
        return self.persisted - self.changed


class DataJudIngestionService:
    """Run the historical and incremental DataJud ingestion flows for one tribunal."""

    def __init__(
        self,
        client: DataJudClient,
        session_factory: SessionFactory,
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

        if page_size <= 0:
            raise ValueError("page_size deve ser maior que zero")

        self.client = client
        self.session_factory = session_factory
        self.tribunal_key = tribunal_key
        self.metadata = metadata
        self.raw_directory = raw_directory
        self.page_size = page_size
        self.incremental_overlap = incremental_overlap

    def run_full(self) -> IngestionReport:
        """Backfill processes with a completion movement in the last six months."""
        run_started_at = datetime.now(UTC)
        window_start = _subtract_calendar_months(run_started_at, 6)
        return self._run(
            mode="full",
            run_started_at=run_started_at,
            completion_window_start=window_start,
            query=_historical_query(window_start, run_started_at),
            include_existing=False,
        )

    def run_incremental(self) -> IngestionReport:
        """Refresh newly finalized processes and updates to known completed ones."""
        checkpoint = self._checkpoint()
        if checkpoint is None:
            raise InitialIngestionRequiredError(
                "Carga histórica ausente. Execute `uv run task full-ingest` primeiro."
            )

        run_started_at = datetime.now(UTC)
        window_start = _subtract_calendar_months(run_started_at, 6)
        return self._run(
            mode="incremental",
            run_started_at=run_started_at,
            completion_window_start=window_start,
            query=_incremental_query(
                checkpoint - self.incremental_overlap,
                run_started_at,
            ),
            include_existing=True,
        )

    def _run(
        self,
        *,
        mode: str,
        run_started_at: datetime,
        completion_window_start: datetime,
        query: dict[str, Any],
        include_existing: bool,
    ) -> IngestionReport:
        run_id = f"{run_started_at.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        search_after: list[Any] | None = None
        pages = 0
        candidates = 0
        persisted = 0
        changed = 0

        while True:
            body = _search_body(
                query,
                page_size=self.page_size,
                search_after=search_after,
            )
            response = self.client.ingest(self.metadata.alias, body)
            hits = _response_hits(response)
            if not hits:
                break

            sources = _source_payloads(hits)
            candidates += len(sources)
            pages += 1

            file_path = save_raw_response(
                self.tribunal_key,
                response,
                run_id=run_id,
                page=pages,
                ingestion_date=run_started_at.date().isoformat(),
                raw_directory=self.raw_directory,
            )
            source_ids = {source["id"] for source in sources}
            existing_ids = (
                self._existing_datajud_ids(source_ids) if include_existing else set()
            )
            included_ids = {
                source["id"]
                for source in sources
                if _has_completion_in_window(
                    source,
                    start=completion_window_start,
                    end=run_started_at,
                )
                or source["id"] in existing_ids
            }

            if included_ids:
                with self.session_factory() as session:
                    result = process_raw_file(
                        file_path,
                        session,
                        raw_directory=self.raw_directory,
                        included_datajud_ids=included_ids,
                        extracted_at=run_started_at,
                    )
                persisted += result.total
                changed += result.changed

            if len(hits) < self.page_size:
                break
            search_after = _last_sort_value(hits[-1])

        self._save_checkpoint(run_started_at)
        return IngestionReport(
            mode=mode,
            run_started_at=run_started_at,
            pages=pages,
            candidates=candidates,
            persisted=persisted,
            changed=changed,
        )

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


def _historical_query(start: datetime, end: datetime) -> dict[str, Any]:
    return {
        "bool": {
            "filter": [
                {"terms": {"movimentos.codigo": sorted(COMPLETION_CODES)}},
                {
                    "range": {
                        "movimentos.dataHora": {
                            "gte": _format_timestamp(start),
                            "lte": _format_timestamp(end),
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
        if start <= occurred_at <= end:
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
