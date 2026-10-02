import gzip
import json
from pathlib import Path
from typing import Any


def save_raw_response(
    tribunal: str,
    payload: dict[str, Any],
    *,
    run_id: str,
    page: int,
    ingestion_date: str,
    raw_directory: Path = Path("data/raw"),
) -> Path:
    """Persist one immutable, compressed DataJud response page."""
    directory = (
        raw_directory
        / tribunal
        / f"ingestion_date={ingestion_date}"
        / f"run_id={run_id}"
    )
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / f"page-{page:06d}.json.gz"
    temporary_path = directory / f".{file_path.name}.part"

    try:
        with gzip.open(
            temporary_path,
            "wt",
            encoding="utf-8",
            compresslevel=6,
        ) as file:
            json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
        temporary_path.replace(file_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return file_path
