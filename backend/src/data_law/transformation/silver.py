import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, or_, select

from data_law.infra.database.model.bronze.bronze_process import (
    BronzeDataJudExtract,
)
from data_law.infra.database.model.silver.movement import SilverDataJudMovement
from data_law.infra.database.model.silver.process import SilverDataJudProcess
from data_law.infra.database.model.silver.subject import SilverDataJudSubject
from data_law.infra.database.session import SessionFactory, create_session_factory
from data_law.ingestion.jurisprudencia import fetch_and_save_precedents_for_subject


@dataclass(frozen=True)
class SilverSyncReport:
    found: int
    synced: int
    movements: int
    warnings: int
    subjects: int = 0


def sync_bronze_to_silver(
    session_factory: SessionFactory,
    *,
    batch_size: int = 500,
) -> SilverSyncReport:
    """Synchronize only missing or changed Bronze extracts into the Silver layer."""
    if batch_size <= 0:
        raise ValueError("batch_size deve ser maior que zero")

    found = 0
    synced = 0
    movements = 0
    subjects = 0
    warnings = 0

    while bronze_ids := _pending_bronze_ids(session_factory, batch_size):
        found += len(bronze_ids)
        for bronze_id in bronze_ids:
            with session_factory() as session:
                with session.begin():
                    extract = session.get(BronzeDataJudExtract, bronze_id)
                    if extract is None:
                        continue

                    process = session.scalar(
                        select(SilverDataJudProcess).where(
                            SilverDataJudProcess.bronze_extract_id == extract.id
                        )
                    )
                    if (
                        process is not None
                        and process.source_payload_hash == extract.payload_hash
                    ):
                        continue

                    process_values, process_warnings = _process_values(extract)
                    movement_values, movement_warnings = _movement_values(
                        extract.payload
                    )
                    subject_values, subject_warnings = _subject_values(
                        extract.payload
                    )
                    extract_warnings = (
                        process_warnings + movement_warnings + subject_warnings
                    )
                    for warning in extract_warnings:
                        print(f"Aviso Silver {extract.datajud_id}: {warning}")
                    warnings += len(extract_warnings)

                    if process is None:
                        process = SilverDataJudProcess(**process_values)
                        session.add(process)
                        session.flush()
                    else:
                        _assign(process, process_values)

                    existing_movements = {
                        movement.source_hash: movement
                        for movement in session.scalars(
                            select(SilverDataJudMovement).where(
                                SilverDataJudMovement.processo_id == process.id,
                            )
                        )
                    }

                    movement_hashes: set[str] = set()
                    for values in movement_values:
                        movement_hash = values["source_hash"]
                        movement_hashes.add(movement_hash)
                        movement = existing_movements.get(movement_hash)
                        if movement is None:
                            session.add(
                                SilverDataJudMovement(
                                    processo_id=process.id,
                                    **values,
                                )
                            )
                        else:
                            _assign(movement, values)

                    stale_movements = delete(SilverDataJudMovement).where(
                        SilverDataJudMovement.processo_id == process.id
                    )
                    if movement_hashes:
                        stale_movements = stale_movements.where(
                            SilverDataJudMovement.source_hash.not_in(movement_hashes)
                        )
                    session.execute(stale_movements)

                    existing_subjects = {
                        subject.source_hash: subject
                        for subject in session.scalars(
                            select(SilverDataJudSubject).where(
                                SilverDataJudSubject.processo_id == process.id,
                            )
                        )
                    }

                    subject_hashes: set[str] = set()
                    for values in subject_values:
                        subject_hash = values["source_hash"]
                        subject_hashes.add(subject_hash)
                        subject = existing_subjects.get(subject_hash)
                        if subject is None:
                            session.add(
                                SilverDataJudSubject(
                                    processo_id=process.id,
                                    **values,
                                )
                            )
                        else:
                            _assign(subject, values)

                    stale_subjects = delete(SilverDataJudSubject).where(
                        SilverDataJudSubject.processo_id == process.id
                    )
                    if subject_hashes:
                        stale_subjects = stale_subjects.where(
                            SilverDataJudSubject.source_hash.not_in(subject_hashes)
                        )
                    session.execute(stale_subjects)

                    synced += 1
                    movements += len(movement_values)
                    subjects += len(subject_values)

                    # Trigger live jurisprudence search for newly inserted subjects
                    for s_val in subject_values:
                        c_code = s_val.get("codigo")
                        c_name = s_val.get("nome")
                        if c_code and c_name and s_val["source_hash"] not in existing_subjects:
                            try:
                                fetch_and_save_precedents_for_subject(
                                    session_factory=session_factory,
                                    assunto_codigo=c_code,
                                    assunto_nome=c_name,
                                    max_precedentes=2,
                                )
                            except Exception:
                                pass

    return SilverSyncReport(
        found=found,
        synced=synced,
        movements=movements,
        subjects=subjects,
        warnings=warnings,
    )


def _pending_bronze_ids(
    session_factory: SessionFactory,
    batch_size: int,
) -> list[UUID]:
    with session_factory() as session:
        statement = (
            select(BronzeDataJudExtract.id)
            .outerjoin(
                SilverDataJudProcess,
                SilverDataJudProcess.bronze_extract_id == BronzeDataJudExtract.id,
            )
            .where(
                or_(
                    SilverDataJudProcess.id.is_(None),
                    SilverDataJudProcess.source_payload_hash
                    != BronzeDataJudExtract.payload_hash,
                )
            )
            .order_by(BronzeDataJudExtract.id)
            .limit(batch_size)
        )
        return list(session.scalars(statement))


def _process_values(
    extract: BronzeDataJudExtract,
) -> tuple[dict[str, Any], list[str]]:
    payload = extract.payload
    warnings: list[str] = []
    classe = _mapping(payload.get("classe"))
    orgao = _mapping(payload.get("orgaoJulgador"))
    formato = _mapping(payload.get("formato"))
    sistema = _mapping(payload.get("sistema"))

    data_ajuizamento = _parse_process_date(
        payload.get("dataAjuizamento"),
        "dataAjuizamento",
        warnings,
    )
    data_ultima_atualizacao = _parse_timestamp(
        payload.get("dataHoraUltimaAtualizacao"),
        "dataHoraUltimaAtualizacao",
        warnings,
    )

    return (
        {
            "bronze_extract_id": extract.id,
            "tribunal_sigla": extract.tribunal_sigla,
            "datajud_id": extract.datajud_id,
            "numero_processo": _string(payload.get("numeroProcesso")),
            "grau": _string(payload.get("grau")),
            "classe_codigo": _integer(classe.get("codigo")),
            "classe_nome": _string(classe.get("nome")),
            "orgao_julgador_codigo": _string(orgao.get("codigo")),
            "orgao_julgador_nome": _string(orgao.get("nome")),
            "orgao_julgador_municipio_ibge": _string(orgao.get("codigoMunicipioIBGE")),
            "formato_codigo": _integer(formato.get("codigo")),
            "formato_nome": _string(formato.get("nome")),
            "sistema_codigo": _integer(sistema.get("codigo")),
            "sistema_nome": _string(sistema.get("nome")),
            "nivel_sigilo": _integer(payload.get("nivelSigilo")),
            "data_ajuizamento": data_ajuizamento,
            "data_hora_ultima_atualizacao": data_ultima_atualizacao,
            "source_file": extract.source_file,
            "source_payload_hash": extract.payload_hash,
            "source_extracted_at": extract.extracted_at,
            "transformed_at": datetime.now(UTC),
        },
        warnings,
    )


def _movement_values(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw_movements = payload.get("movimentos")
    if raw_movements is None:
        return [], []
    if not isinstance(raw_movements, list):
        return [], ["movimentos não é uma lista"]

    values: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_hashes: set[str] = set()
    for position, raw_movement in enumerate(raw_movements):
        if not isinstance(raw_movement, dict):
            warnings.append(f"movimento {position} inválido foi ignorado")
            continue

        source_hash = _canonical_hash(raw_movement)
        if source_hash in seen_hashes:
            continue
        seen_hashes.add(source_hash)

        orgao = _mapping(raw_movement.get("orgaoJulgador"))
        values.append(
            {
                "source_hash": source_hash,
                "codigo": _integer(raw_movement.get("codigo")),
                "nome": _string(raw_movement.get("nome")),
                "data_hora": _parse_timestamp(
                    raw_movement.get("dataHora"),
                    f"movimento {position}.dataHora",
                    warnings,
                ),
                "orgao_julgador_codigo": _string(orgao.get("codigo")),
                "orgao_julgador_nome": _string(orgao.get("nome")),
                "complementos_tabelados": raw_movement.get("complementosTabelados"),
            }
        )

    return values, warnings


def _subject_values(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw_subjects = payload.get("assuntos")
    if raw_subjects is None:
        return [], []
    if not isinstance(raw_subjects, list):
        return [], ["assuntos não é uma lista"]

    values: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_hashes: set[str] = set()
    for position, raw_subject in enumerate(raw_subjects):
        if not isinstance(raw_subject, dict):
            warnings.append(f"assunto {position} inválido foi ignorado")
            continue

        source_hash = _canonical_hash(raw_subject)
        if source_hash in seen_hashes:
            continue
        seen_hashes.add(source_hash)

        principal = raw_subject.get("principal")
        values.append(
            {
                "source_hash": source_hash,
                "codigo": _integer(raw_subject.get("codigo")),
                "nome": _string(raw_subject.get("nome")),
                "principal": principal if isinstance(principal, bool) else None,
            }
        )

    return values, warnings


def _canonical_hash(value: dict[str, Any]) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _assign(instance: object, values: dict[str, Any]) -> None:
    for key, value in values.items():
        setattr(instance, key, value)


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _parse_process_date(
    value: object,
    field: str,
    warnings: list[str],
) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None

    normalized = value.strip()
    try:
        if normalized.isdigit() and len(normalized) == 14:
            return datetime.strptime(normalized, "%Y%m%d%H%M%S").date()
        if normalized.isdigit() and len(normalized) == 8:
            return datetime.strptime(normalized, "%Y%m%d").date()
        timestamp = _parse_timestamp(normalized, field, warnings)
        return timestamp.date() if timestamp is not None else None
    except ValueError:
        warnings.append(f"{field} inválido")
        return None


def _parse_timestamp(
    value: object,
    field: str,
    warnings: list[str],
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        warnings.append(f"{field} inválido")
        return None
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )


def main() -> None:
    report = sync_bronze_to_silver(create_session_factory())
    print(
        f"Silver sincronizada: {report.synced} processo(s), "
        f"{report.movements} movimento(s), {report.subjects} assunto(s), "
        f"{report.warnings} aviso(s)."
    )


if __name__ == "__main__":
    main()
