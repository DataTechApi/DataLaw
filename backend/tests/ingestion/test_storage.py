import gzip
import json
from pathlib import Path

import pytest

from data_law.ingestion.storage import save_raw_response


def test_save_raw_response_writes_a_partitioned_gzip_file(tmp_path: Path) -> None:
    payload = {"hits": {"hits": [{"_source": {"id": "123"}}]}}

    file_path = save_raw_response(
        "tjsp",
        payload,
        run_id="20260921T010203Z-abcdef12",
        page=1,
        ingestion_date="2026-09-21",
        raw_directory=tmp_path / "data" / "raw",
    )

    assert file_path == (
        tmp_path
        / "data/raw/tjsp/ingestion_date=2026-09-21"
        / "run_id=20260921T010203Z-abcdef12/page-000001.json.gz"
    )
    with gzip.open(file_path, "rt", encoding="utf-8") as file:
        assert json.load(file) == payload


def test_save_raw_response_removes_partial_file_when_serialization_fails(
    tmp_path: Path,
) -> None:
    raw_directory = tmp_path / "data" / "raw"

    with pytest.raises(TypeError):
        save_raw_response(
            "tjsp",
            {"hits": {"ids": {"nao-serializavel"}}},
            run_id="20260921T010203Z-abcdef12",
            page=2,
            ingestion_date="2026-09-21",
            raw_directory=raw_directory,
        )

    directory = (
        raw_directory
        / "tjsp/ingestion_date=2026-09-21/run_id=20260921T010203Z-abcdef12"
    )
    assert list(directory.iterdir()) == []
