import gzip
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from data_law.infra.database.model.bronze.bronze_process import (
    BronzeDataJudExtract,
)
from data_law.infra.database.session import create_session_factory

RAW_DIRECTORY = Path("data/raw")


@dataclass(frozen=True)
class TribunalMetadata:
    alias: str
    sigla: str


TRIBUNAL_METADATA = {
    "tjsp": TribunalMetadata(alias="api_publica_tjsp", sigla="TJSP"),
}


@dataclass(frozen=True)
class ProcessedFile:
    source_file: str
    total: int
    changed: int

    @property
    def unchanged(self) -> int:
        return self.total - self.changed


class BronzeProcessingError(ValueError):
    """Raised when a raw DataJud file cannot be persisted safely."""


def payload_hash(payload: dict[str, Any]) -> str:
    """Return a stable hash for a JSON object, independent of key order."""
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _read_process_payloads(file_path: Path) -> list[dict[str, Any]]:
    try:
        if file_path.suffix == ".gz":
            with gzip.open(file_path, "rt", encoding="utf-8") as file:
                document = json.load(file)
        else:
            with file_path.open("r", encoding="utf-8") as file:
                document = json.load(file)
    except json.JSONDecodeError as error:
        raise BronzeProcessingError(f"JSON inválido: {file_path}") from error

    if not isinstance(document, dict):
        raise BronzeProcessingError(
            f"A resposta precisa ser um objeto JSON: {file_path}"
        )

    hits = document.get("hits")
    hit_list = hits.get("hits") if isinstance(hits, dict) else None
    if not isinstance(hit_list, list):
        raise BronzeProcessingError(f"Resposta DataJud sem hits.hits: {file_path}")

    process_payloads: list[dict[str, Any]] = []
    for position, hit in enumerate(hit_list):
        source = hit.get("_source") if isinstance(hit, dict) else None
        if not isinstance(source, dict):
            raise BronzeProcessingError(
                f"Hit {position} sem _source válido em {file_path}"
            )

        datajud_id = source.get("id")
        if not isinstance(datajud_id, str) or not datajud_id.strip():
            raise BronzeProcessingError(
                f"Hit {position} sem _source.id válido em {file_path}"
            )
        process_payloads.append(source)

    return process_payloads


def _metadata_for_file(file_path: Path, raw_directory: Path) -> TribunalMetadata:
    try:
        relative_path = file_path.resolve().relative_to(raw_directory.resolve())
    except ValueError as error:
        raise BronzeProcessingError(
            f"Arquivo fora de {raw_directory}: {file_path}"
        ) from error

    if len(relative_path.parts) < 2:
        raise BronzeProcessingError(
            f"Arquivo deve estar em um diretório de tribunal: {file_path}"
        )

    tribunal_key = relative_path.parts[0].lower()
    try:
        return TRIBUNAL_METADATA[tribunal_key]
    except KeyError as error:
        raise BronzeProcessingError(
            f"Tribunal sem mapeamento para {tribunal_key}: {file_path}"
        ) from error


def _source_file(file_path: Path, raw_directory: Path) -> str:
    project_root = raw_directory.resolve().parent.parent
    return file_path.resolve().relative_to(project_root).as_posix()


def _upsert_process(
    session: Session,
    *,
    metadata: TribunalMetadata,
    source_file: str,
    extracted_at: datetime,
    payload: dict[str, Any],
) -> bool:
    datajud_id = payload["id"]
    payload_digest = payload_hash(payload)
    statement = insert(BronzeDataJudExtract).values(
        tribunal_alias=metadata.alias,
        tribunal_sigla=metadata.sigla,
        datajud_id=datajud_id,
        source_file=source_file,
        extracted_at=extracted_at,
        payload_hash=payload_digest,
        payload=payload,
    )
    upsert_statement = statement.on_conflict_do_update(
        constraint="uq_bronze_datajud_extract_tribunal_datajud_id",
        set_={
            "tribunal_alias": statement.excluded.tribunal_alias,
            "source_file": statement.excluded.source_file,
            "extracted_at": statement.excluded.extracted_at,
            "payload_hash": statement.excluded.payload_hash,
            "payload": statement.excluded.payload,
        },
        where=BronzeDataJudExtract.payload_hash.is_distinct_from(
            statement.excluded.payload_hash
        ),
    ).returning(BronzeDataJudExtract.id)
    return session.execute(upsert_statement).scalar_one_or_none() is not None


def process_raw_file(
    file_path: Path,
    session: Session,
    raw_directory: Path = RAW_DIRECTORY,
    included_datajud_ids: set[str] | None = None,
    extracted_at: datetime | None = None,
) -> ProcessedFile:
    """Persist selected DataJud processes from one raw response atomically."""
    metadata = _metadata_for_file(file_path, raw_directory)
    source_file = _source_file(file_path, raw_directory)
    process_payloads = _read_process_payloads(file_path)
    if included_datajud_ids is not None:
        process_payloads = [
            payload
            for payload in process_payloads
            if payload["id"] in included_datajud_ids
        ]
    effective_extracted_at = extracted_at or datetime.now(UTC)
    changed = 0

    with session.begin():
        for process_payload in process_payloads:
            changed += _upsert_process(
                session,
                metadata=metadata,
                source_file=source_file,
                extracted_at=effective_extracted_at,
                payload=process_payload,
            )

    return ProcessedFile(
        source_file=source_file,
        total=len(process_payloads),
        changed=changed,
    )


def process_raw_directory(
    raw_directory: Path = RAW_DIRECTORY,
    session_factory: Callable[[], Session] | None = None,
) -> list[ProcessedFile]:
    """Process raw JSON files in lexical order, stopping at the first failure."""
    factory = session_factory or create_session_factory()
    files = sorted(
        path
        for pattern in ("*.json", "*.json.gz")
        for path in raw_directory.rglob(pattern)
        if path.is_file()
    )
    processed_files: list[ProcessedFile] = []

    for file_path in files:
        with factory() as session:
            processed_files.append(process_raw_file(file_path, session, raw_directory))

    return processed_files


def main() -> None:
    processed_files = process_raw_directory()
    total = sum(item.total for item in processed_files)
    changed = sum(item.changed for item in processed_files)
    print(
        f"Bronze processada: {len(processed_files)} arquivo(s), "
        f"{total} processo(s), {changed} alteração(ões)."
    )


if __name__ == "__main__":
    main()
