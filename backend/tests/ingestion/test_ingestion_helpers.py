from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from data_law.ingestion.ingestion import (
    DataJudIngestionError,
    IngestionReport,
    _as_utc,
    _has_completion_in_window,
    _last_sort_value,
    _response_hits,
    _source_payloads,
    _subtract_calendar_months,
)

START = datetime(2026, 3, 1, tzinfo=UTC)
END = datetime(2026, 3, 31, tzinfo=UTC)


def _process(*movements: Any) -> dict[str, Any]:
    return {"id": "1234", "movimentos": list(movements)}


def test_response_hits_returns_hit_list() -> None:
    hits = [{"_source": {"id": "1"}}]

    assert _response_hits({"timed_out": False, "hits": {"hits": hits}}) == hits


@pytest.mark.parametrize(
    ("response", "error"),
    [
        ({"timed_out": True, "hits": {"hits": []}}, "tempo limite"),
        ({}, "hits.hits"),
        ({"hits": []}, "hits.hits"),
        ({"hits": {"hits": {}}}, "hits.hits"),
        ({"hits": {"hits": ["texto"]}}, "hits.hits"),
    ],
)
def test_response_hits_rejects_invalid_responses(
    response: dict[str, Any],
    error: str,
) -> None:
    with pytest.raises(DataJudIngestionError, match=error):
        _response_hits(response)


@pytest.mark.parametrize(
    ("hits", "error"),
    [
        ([{"sort": []}], "Hit 0 da API sem _source válido"),
        ([{"_source": {"id": "1"}}, {"_source": []}], "Hit 1 da API sem _source"),
        ([{"_source": {"id": "  "}}], "sem _source.id válido"),
        ([{"_source": {"id": 123}}], "sem _source.id válido"),
    ],
)
def test_source_payloads_rejects_hits_without_valid_source(
    hits: list[dict[str, Any]],
    error: str,
) -> None:
    with pytest.raises(DataJudIngestionError, match=error):
        _source_payloads(hits)


def test_source_payloads_returns_sources_in_order() -> None:
    hits = [{"_source": {"id": "1"}}, {"_source": {"id": "2"}}]

    assert _source_payloads(hits) == [{"id": "1"}, {"id": "2"}]


@pytest.mark.parametrize("sort", [None, "cursor", ["somente-um"], [1, 2, 3]])
def test_last_sort_value_requires_two_part_cursor(sort: Any) -> None:
    with pytest.raises(DataJudIngestionError, match="cursor de paginação"):
        _last_sort_value({"sort": sort})


def test_last_sort_value_returns_cursor() -> None:
    assert _last_sort_value({"sort": ["2026-03-01", "1"]}) == ["2026-03-01", "1"]


@pytest.mark.parametrize(
    "process",
    [
        {"id": "1234"},
        {"id": "1234", "movimentos": "invalido"},
        _process("texto"),
        _process({"codigo": 970, "dataHora": "2026-03-10T10:00:00Z"}),
        _process({"codigo": 22}),
        _process({"codigo": 22, "dataHora": 20260310}),
        _process({"codigo": 22, "dataHora": "10/03/2026"}),
        _process({"codigo": 246, "dataHora": "2026-02-28T23:59:59Z"}),
        _process({"codigo": 246, "dataHora": "2026-04-01T00:00:00Z"}),
    ],
)
def test_has_completion_in_window_ignores_invalid_or_outside_movements(
    process: dict[str, Any],
) -> None:
    assert not _has_completion_in_window(process, start=START, end=END)


@pytest.mark.parametrize(
    "date_time",
    [
        "2026-03-01T00:00:00Z",
        "2026-03-15T12:00:00-03:00",
        "2026-03-31T00:00:00+00:00",
        "2026-03-20T10:00:00",
    ],
)
def test_has_completion_in_window_accepts_completion_inside_window(
    date_time: str,
) -> None:
    process = _process(
        "texto",
        {"codigo": 22, "dataHora": "invalida"},
        {"codigo": 246, "dataHora": date_time},
    )

    assert _has_completion_in_window(process, start=START, end=END)


@pytest.mark.parametrize(
    ("value", "months", "expected"),
    [
        (datetime(2026, 9, 15, tzinfo=UTC), 6, datetime(2026, 3, 15, tzinfo=UTC)),
        (datetime(2026, 3, 10, tzinfo=UTC), 6, datetime(2025, 9, 10, tzinfo=UTC)),
        (datetime(2026, 8, 31, tzinfo=UTC), 6, datetime(2026, 2, 28, tzinfo=UTC)),
        (datetime(2028, 8, 31, tzinfo=UTC), 6, datetime(2028, 2, 29, tzinfo=UTC)),
        (datetime(2026, 1, 31, tzinfo=UTC), 0, datetime(2026, 1, 31, tzinfo=UTC)),
    ],
)
def test_subtract_calendar_months_clamps_to_month_end(
    value: datetime,
    months: int,
    expected: datetime,
) -> None:
    assert _subtract_calendar_months(value, months) == expected


def test_as_utc_assumes_utc_for_naive_values() -> None:
    assert _as_utc(datetime(2026, 3, 1, 12, 0)) == datetime(
        2026, 3, 1, 12, 0, tzinfo=UTC
    )


def test_as_utc_converts_aware_values() -> None:
    brasilia = timezone(timedelta(hours=-3))

    result = _as_utc(datetime(2026, 3, 1, 9, 0, tzinfo=brasilia))

    assert result == datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    assert result.tzinfo is UTC


def test_ingestion_report_counts_unchanged_processes() -> None:
    report = IngestionReport(
        mode="full",
        run_started_at=START,
        pages=1,
        candidates=5,
        persisted=4,
        changed=1,
    )

    assert report.unchanged == 3
