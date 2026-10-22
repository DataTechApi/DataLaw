import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import pytest

from data_law.infra.database.model.bronze.bronze_process import BronzeDataJudExtract
from data_law.infra.database.model.silver.movement import SilverDataJudMovement
from data_law.infra.database.model.silver.process import SilverDataJudProcess
from data_law.infra.database.model.silver.subject import SilverDataJudSubject
from data_law.transformation import silver
from data_law.transformation.silver import (
    _canonical_hash,
    _pending_bronze_ids,
    sync_bronze_to_silver,
)

DISTRIBUICAO = {
    "codigo": 26,
    "nome": "Distribuição",
    "dataHora": "2026-03-01T10:00:00Z",
}
CONCLUSAO = {"codigo": 51, "nome": "Conclusão", "dataHora": "2026-03-05T10:00:00Z"}
SENTENCA = {"codigo": 246, "nome": "Definitivo", "dataHora": "2026-03-20T10:00:00Z"}
DANO_MORAL = {"codigo": 10433, "nome": "Indenização por Dano Moral", "principal": True}
CONSUMIDOR = {"codigo": 7779, "nome": "Responsabilidade do Fornecedor"}


class FakeDatabase:
    """In-memory stand-in for the tables touched by the Silver sync."""

    def __init__(self) -> None:
        self.extracts: dict[uuid.UUID, BronzeDataJudExtract] = {}
        self.processes: list[SilverDataJudProcess] = []
        self.movements: list[SilverDataJudMovement] = []
        self.subjects: list[SilverDataJudSubject] = []
        self.sessions = 0

    def add_extract(self, payload: dict[str, Any], **fields: Any) -> uuid.UUID:
        extract = BronzeDataJudExtract(
            id=uuid.uuid4(),
            tribunal_alias="api_publica_tjsp",
            tribunal_sigla="TJSP",
            datajud_id=fields.get("datajud_id", f"TJSP_{len(self.extracts)}"),
            source_file="raw/tjsp/page-1.json.gz",
            extracted_at=datetime(2026, 3, 2, tzinfo=UTC),
            payload_hash=fields.get("payload_hash", _canonical_hash(payload)),
            payload=payload,
        )
        self.extracts[extract.id] = extract
        return extract.id

    def add_process(self, extract_id: uuid.UUID, **fields: Any) -> uuid.UUID:
        process = SilverDataJudProcess(
            id=uuid.uuid4(), bronze_extract_id=extract_id, **fields
        )
        self.processes.append(process)
        return process.id

    def session(self) -> "FakeSession":
        self.sessions += 1
        return FakeSession(self)


class FakeSession:
    def __init__(self, database: FakeDatabase) -> None:
        self.db = database

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    @contextmanager
    def begin(self):
        yield self

    def get(self, model: type[object], key: uuid.UUID) -> object | None:
        assert model is BronzeDataJudExtract
        return self.db.extracts.get(key)

    def scalar(self, statement: Any) -> SilverDataJudProcess | None:
        assert statement.column_descriptions[0]["entity"] is SilverDataJudProcess
        extract_id = statement.whereclause.right.value
        return next(
            (p for p in self.db.processes if p.bronze_extract_id == extract_id),
            None,
        )

    def scalars(self, statement: Any) -> list[Any]:
        entity = statement.column_descriptions[0]["entity"]
        process_id = statement.whereclause.right.value
        rows = self._rows(entity)
        return [row for row in rows if row.processo_id == process_id]

    def add(self, item: object) -> None:
        self._rows(type(item)).append(item)

    def flush(self) -> None:
        for process in self.db.processes:
            if process.id is None:
                process.id = uuid.uuid4()

    def execute(self, statement: Any) -> None:
        entity = statement.entity_description["entity"]
        criteria = statement._where_criteria
        process_id = criteria[0].right.value
        kept = set(criteria[1].right.value) if len(criteria) > 1 else set()
        rows = self._rows(entity)
        rows[:] = [
            row
            for row in rows
            if row.processo_id != process_id or row.source_hash in kept
        ]

    def _rows(self, entity: type[object]) -> list[Any]:
        if entity is SilverDataJudProcess:
            return self.db.processes
        if entity is SilverDataJudMovement:
            return self.db.movements
        if entity is SilverDataJudSubject:
            return self.db.subjects
        raise AssertionError(f"tabela inesperada: {entity}")


@pytest.fixture
def db() -> FakeDatabase:
    return FakeDatabase()


@pytest.fixture
def pending(monkeypatch: pytest.MonkeyPatch, db: FakeDatabase) -> list[list[uuid.UUID]]:
    """Batches returned by _pending_bronze_ids, consumed in order."""
    batches: list[list[uuid.UUID]] = []

    def fake_pending(session_factory: object, batch_size: int) -> list[uuid.UUID]:
        return batches.pop(0) if batches else []

    monkeypatch.setattr(silver, "_pending_bronze_ids", fake_pending)
    return batches


@pytest.fixture
def bnp_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_fetch(**kwargs: Any) -> int:
        calls.append(kwargs)
        return 0

    monkeypatch.setattr(silver, "fetch_and_save_precedents_for_subject", fake_fetch)
    return calls


def _payload(**overrides: Any) -> dict[str, Any]:
    return {
        "numeroProcesso": "00000010220268260100",
        "classe": {"codigo": 7, "nome": "Procedimento Comum Cível"},
        "dataAjuizamento": "20260301120000",
        "movimentos": [DISTRIBUICAO, CONCLUSAO],
        "assuntos": [DANO_MORAL],
        **overrides,
    }


def test_rejects_non_positive_batch_size(db: FakeDatabase) -> None:
    with pytest.raises(ValueError, match="batch_size"):
        sync_bronze_to_silver(db.session, batch_size=0)


def test_returns_empty_report_when_nothing_is_pending(
    db: FakeDatabase, pending: list[list[uuid.UUID]]
) -> None:
    report = sync_bronze_to_silver(db.session)

    assert report == silver.SilverSyncReport(
        found=0, synced=0, movements=0, warnings=0, subjects=0
    )


def test_inserts_new_process_with_movements_and_subjects(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    extract_id = db.add_extract(_payload())
    pending.append([extract_id])

    report = sync_bronze_to_silver(db.session)

    assert report == silver.SilverSyncReport(
        found=1, synced=1, movements=2, warnings=0, subjects=1
    )
    [process] = db.processes
    assert process.id is not None
    assert process.bronze_extract_id == extract_id
    assert process.numero_processo == "00000010220268260100"
    assert process.classe_nome == "Procedimento Comum Cível"
    assert process.source_payload_hash == db.extracts[extract_id].payload_hash
    assert {m.codigo for m in db.movements} == {26, 51}
    assert all(m.processo_id == process.id for m in db.movements)
    [subject] = db.subjects
    assert subject.processo_id == process.id
    assert subject.codigo == 10433
    assert subject.principal is True


def test_searches_precedents_for_each_new_subject(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    pending.append([db.add_extract(_payload(assuntos=[DANO_MORAL, CONSUMIDOR]))])

    sync_bronze_to_silver(db.session)

    assert [
        (call["assunto_codigo"], call["assunto_nome"], call["max_precedentes"])
        for call in bnp_calls
    ] == [
        (10433, "Indenização por Dano Moral", 2),
        (7779, "Responsabilidade do Fornecedor", 2),
    ]
    assert all(call["session_factory"] == db.session for call in bnp_calls)


def test_skips_precedent_search_for_subject_without_code_or_name(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    pending.append(
        [db.add_extract(_payload(assuntos=[{"nome": "Sem código"}, {"codigo": 1}]))]
    )

    report = sync_bronze_to_silver(db.session)

    assert report.subjects == 2
    assert bnp_calls == []


def test_precedent_search_failure_does_not_stop_sync(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_fetch(**kwargs: Any) -> int:
        raise RuntimeError("BNP fora do ar")

    monkeypatch.setattr(silver, "fetch_and_save_precedents_for_subject", failing_fetch)
    first = db.add_extract(_payload())
    second = db.add_extract(_payload(numeroProcesso="2"))
    pending.append([first, second])

    report = sync_bronze_to_silver(db.session)

    assert report.synced == 2
    assert len(db.processes) == 2


def test_skips_process_whose_payload_hash_did_not_change(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    extract_id = db.add_extract(_payload(), payload_hash="h1")
    db.add_process(extract_id, source_payload_hash="h1", numero_processo="antigo")
    pending.append([extract_id])

    report = sync_bronze_to_silver(db.session)

    assert report.found == 1
    assert report.synced == 0
    assert db.processes[0].numero_processo == "antigo"
    assert db.movements == []
    assert bnp_calls == []


def test_ignores_extract_that_no_longer_exists(
    db: FakeDatabase, pending: list[list[uuid.UUID]]
) -> None:
    pending.append([uuid.uuid4()])

    report = sync_bronze_to_silver(db.session)

    assert report.found == 1
    assert report.synced == 0
    assert db.processes == []


def test_updates_changed_process_and_replaces_stale_children(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    extract_id = db.add_extract(
        _payload(
            numeroProcesso="novo",
            movimentos=[DISTRIBUICAO, SENTENCA],
            assuntos=[DANO_MORAL, CONSUMIDOR],
        ),
        payload_hash="h2",
    )
    process_id = db.add_process(
        extract_id, source_payload_hash="h1", numero_processo="antigo"
    )
    kept_movement = SilverDataJudMovement(
        processo_id=process_id,
        source_hash=_canonical_hash(DISTRIBUICAO),
        nome="nome antigo",
    )
    db.movements.extend(
        [
            kept_movement,
            SilverDataJudMovement(
                processo_id=process_id, source_hash=_canonical_hash(CONCLUSAO)
            ),
        ]
    )
    db.subjects.append(
        SilverDataJudSubject(
            processo_id=process_id, source_hash=_canonical_hash(DANO_MORAL)
        )
    )
    other_process_movement = SilverDataJudMovement(
        processo_id=uuid.uuid4(), source_hash=_canonical_hash(CONCLUSAO)
    )
    db.movements.append(other_process_movement)
    pending.append([extract_id])

    report = sync_bronze_to_silver(db.session)

    assert report.synced == 1
    [process] = db.processes
    assert process.id == process_id
    assert process.numero_processo == "novo"
    assert process.source_payload_hash == "h2"

    own_movements = [m for m in db.movements if m.processo_id == process_id]
    assert {m.codigo for m in own_movements} == {26, 246}
    assert kept_movement in own_movements
    assert kept_movement.nome == "Distribuição"
    assert other_process_movement in db.movements

    assert {s.source_hash for s in db.subjects} == {
        _canonical_hash(DANO_MORAL),
        _canonical_hash(CONSUMIDOR),
    }
    assert [call["assunto_codigo"] for call in bnp_calls] == [7779]


def test_removes_all_children_when_payload_has_none(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    extract_id = db.add_extract(_payload(movimentos=[], assuntos=None))
    process_id = db.add_process(extract_id, source_payload_hash="antigo")
    db.movements.append(SilverDataJudMovement(processo_id=process_id, source_hash="m1"))
    db.subjects.append(SilverDataJudSubject(processo_id=process_id, source_hash="s1"))
    pending.append([extract_id])

    report = sync_bronze_to_silver(db.session)

    assert report.synced == 1
    assert report.movements == 0
    assert report.subjects == 0
    assert db.movements == []
    assert db.subjects == []


def test_counts_and_prints_warnings(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    extract_id = db.add_extract(
        _payload(
            dataAjuizamento="20261301",
            movimentos=[DISTRIBUICAO, "invalido"],
            assuntos="10433",
        ),
        datajud_id="TJSP_123",
    )
    pending.append([extract_id])

    report = sync_bronze_to_silver(db.session)

    assert report.warnings == 3
    assert report.synced == 1
    assert report.movements == 1
    output = capsys.readouterr().out
    assert "Aviso Silver TJSP_123: dataAjuizamento inválido" in output
    assert "Aviso Silver TJSP_123: movimento 1 inválido foi ignorado" in output
    assert "Aviso Silver TJSP_123: assuntos não é uma lista" in output


def test_processes_every_pending_batch(
    db: FakeDatabase,
    pending: list[list[uuid.UUID]],
    bnp_calls: list[dict[str, Any]],
) -> None:
    ids = [db.add_extract(_payload(numeroProcesso=str(n))) for n in range(3)]
    pending.extend([ids[:2], ids[2:]])

    report = sync_bronze_to_silver(db.session, batch_size=2)

    assert report.found == 3
    assert report.synced == 3
    assert report.movements == 6
    assert sorted(p.numero_processo for p in db.processes) == ["0", "1", "2"]


def test_pending_bronze_ids_selects_missing_or_changed_extracts() -> None:
    expected = [uuid.uuid4(), uuid.uuid4()]
    statements: list[Any] = []

    class CapturingSession(FakeSession):
        def scalars(self, statement: Any) -> list[uuid.UUID]:
            statements.append(statement)
            return expected

    result = _pending_bronze_ids(lambda: CapturingSession(FakeDatabase()), 25)

    assert result == expected
    sql = " ".join(str(statements[0]).split())
    assert "LEFT OUTER JOIN silver.processo" in sql
    assert "silver.processo.id IS NULL" in sql
    assert (
        "silver.processo.source_payload_hash != bronze.datajud_extract.payload_hash"
        in sql
    )
    assert "ORDER BY bronze.datajud_extract.id" in sql
    assert statements[0]._limit == 25
