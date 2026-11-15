from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from data_law.infra.database.model.silver.precedent_direction import (
    PRECEDENT_DIRECTIONS,
    SilverPrecedentDirection,
)


def test_precedent_direction_mapping() -> None:
    table = SilverPrecedentDirection.__table__

    assert table.schema == "silver"
    assert table.name == "precedente_direcao"
    assert set(table.columns.keys()) == {
        "id",
        "jurisprudencia_id",
        "direcao",
        "curador",
        "curado_em",
    }
    assert isinstance(table.c.id.type, UUID)
    assert not table.c.direcao.nullable
    assert not table.c.curador.nullable
    assert table.c.curado_em.server_default is not None

    foreign_key = next(iter(table.c.jurisprudencia_id.foreign_keys))
    assert foreign_key.target_fullname == "silver.jurisprudencia.id"
    assert foreign_key.ondelete == "CASCADE"

    unique = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert [list(c.columns.keys()) for c in unique] == [["jurisprudencia_id"]]


def test_precedent_direction_accepts_only_known_directions() -> None:
    table = SilverPrecedentDirection.__table__
    check = next(c for c in table.constraints if isinstance(c, CheckConstraint))

    assert PRECEDENT_DIRECTIONS == ("autor", "reu", "indefinida")
    assert str(check.sqltext) == "direcao IN ('autor', 'reu', 'indefinida')"
