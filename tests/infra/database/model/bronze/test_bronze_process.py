import uuid

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from data_law.infra.database.model.bronze.bronze_process import BronzeDataJudExtract
from data_law.infra.database.model.bronze.ingestion_state import (
    BronzeDataJudIngestionState,
)


def test_datajud_extract_mapping() -> None:
    table = BronzeDataJudExtract.__table__

    assert table.schema == "bronze"
    assert table.name == "datajud_extract"
    assert set(table.columns.keys()) == {
        "id",
        "tribunal_alias",
        "tribunal_sigla",
        "datajud_id",
        "source_file",
        "extracted_at",
        "payload_hash",
        "payload",
    }
    assert table.c.id.primary_key
    assert isinstance(table.c.id.type, UUID)
    assert table.c.id.default is not None
    assert isinstance(table.c.id.default.arg(None), uuid.UUID)
    assert isinstance(table.c.payload.type, JSONB)
    assert table.c.payload_hash.type.length == 64

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    assert tuple(unique_constraints[0].columns.keys()) == (
        "tribunal_sigla",
        "datajud_id",
    )


def test_ingestion_state_mapping() -> None:
    table = BronzeDataJudIngestionState.__table__

    assert table.schema == "bronze"
    assert table.name == "datajud_ingestion_state"
    assert list(table.c.keys()) == [
        "tribunal_alias",
        "tribunal_sigla",
        "last_successful_at",
    ]
    assert table.c.tribunal_alias.primary_key
