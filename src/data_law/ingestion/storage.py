import json
from datetime import datetime, UTC
from pathlib import Path

def save_raw_response(tribunal: str, payload: dict) -> Path:
    directory = Path("data/raw")  / tribunal
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    file_path = directory / f"{timestamp}.json"

    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return file_path
    