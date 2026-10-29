import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from data_law.infra.database.model.bronze.bronze_process import BronzeDataJudExtract
from data_law.transformation.silver import (
    _assign,
    _canonical_hash,
    _integer,
    _mapping,
    _movement_values,
    _parse_process_date,
    _parse_timestamp,
    _process_values,
    _string,
    _subject_values,
)


def _extract(payload: dict[str, Any]) -> BronzeDataJudExtract:
    return BronzeDataJudExtract(
        id=uuid.uuid4(),
        tribunal_alias="api_publica_tjsp",
        tribunal_sigla="TJSP",
        datajud_id="TJSP_JE_00000001020268260100",
        source_file="raw/tjsp/2026/03/01/page-1.json.gz",
        extracted_at=datetime(2026, 3, 2, 8, 0, tzinfo=UTC),
        payload_hash="a" * 64,
        payload=payload,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Procedimento Comum  ", "Procedimento Comum"),
        ("   ", None),
        ("", None),
        (12, "12"),
        (1.5, "1.5"),
        (True, None),
        (None, None),
        (["a"], None),
    ],
)
def test_string_strips_text_and_converts_numbers(value: object, expected: str) -> None:
    assert _string(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (7, 7),
        ("12", 12),
        (" 12 ", 12),
        ("abc", None),
        ("1.5", None),
        (1.5, None),
        (True, None),
        (False, None),
        (None, None),
    ],
)
def test_integer_accepts_only_integers_and_numeric_strings(
    value: object, expected: int | None
) -> None:
    assert _integer(value) == expected


@pytest.mark.parametrize("value", [None, "texto", [1], 3])
def test_mapping_returns_empty_dict_for_non_dict(value: object) -> None:
    assert _mapping(value) == {}


def test_mapping_returns_same_dict() -> None:
    value = {"codigo": 1}

    assert _mapping(value) is value


def test_assign_sets_every_value_on_instance() -> None:
    instance = SimpleNamespace(nome="antigo", codigo=1)

    _assign(instance, {"nome": "novo", "grau": "G1"})

    assert instance.nome == "novo"
    assert instance.codigo == 1
    assert instance.grau == "G1"


def test_canonical_hash_ignores_key_order_and_keeps_unicode() -> None:
    first = {"nome": "Indenização", "codigo": 1}
    second = {"codigo": 1, "nome": "Indenização"}

    assert _canonical_hash(first) == _canonical_hash(second)
    assert _canonical_hash(first) != _canonical_hash({**first, "codigo": 2})
    assert len(_canonical_hash(first)) == 64


def test_canonical_hash_rejects_nan() -> None:
    with pytest.raises(ValueError):
        _canonical_hash({"valor": float("nan")})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-03-01T10:00:00Z", datetime(2026, 3, 1, 10, 0, tzinfo=UTC)),
        ("2026-03-01T10:00:00.123Z", datetime(2026, 3, 1, 10, 0, 0, 123000, UTC)),
        ("2026-03-01T10:00:00-03:00", datetime(2026, 3, 1, 13, 0, tzinfo=UTC)),
        ("2026-03-01T10:00:00", datetime(2026, 3, 1, 10, 0, tzinfo=UTC)),
        ("  2026-03-01T10:00:00Z  ", datetime(2026, 3, 1, 10, 0, tzinfo=UTC)),
    ],
)
def test_parse_timestamp_normalizes_to_utc(value: str, expected: datetime) -> None:
    warnings: list[str] = []

    parsed = _parse_timestamp(value, "campo", warnings)

    assert parsed == expected
    assert parsed is not None and parsed.utcoffset() == timedelta(0)
    assert warnings == []


@pytest.mark.parametrize("value", [None, "", "   ", 20260301, ["2026-03-01"]])
def test_parse_timestamp_ignores_missing_values_without_warning(
    value: object,
) -> None:
    warnings: list[str] = []

    assert _parse_timestamp(value, "campo", warnings) is None
    assert warnings == []


@pytest.mark.parametrize("value", ["ontem", "2026-02-30T10:00:00Z", "01/03/2026"])
def test_parse_timestamp_warns_on_invalid_value(value: str) -> None:
    warnings: list[str] = []

    assert _parse_timestamp(value, "dataHora", warnings) is None
    assert warnings == ["dataHora inválido"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("20260301120000", date(2026, 3, 1)),
        ("20260301", date(2026, 3, 1)),
        ("2026-03-01T10:00:00Z", date(2026, 3, 1)),
        ("2026-03-01", date(2026, 3, 1)),
        (" 20260301 ", date(2026, 3, 1)),
    ],
)
def test_parse_process_date_accepts_datajud_formats(value: str, expected: date) -> None:
    warnings: list[str] = []

    assert _parse_process_date(value, "dataAjuizamento", warnings) == expected
    assert warnings == []


@pytest.mark.parametrize("value", [None, "", "  ", 20260301])
def test_parse_process_date_ignores_missing_values_without_warning(
    value: object,
) -> None:
    warnings: list[str] = []

    assert _parse_process_date(value, "dataAjuizamento", warnings) is None
    assert warnings == []


@pytest.mark.parametrize(
    "value", ["20261301", "20260230120000", "20260301250000", "2026-13-01", "abc"]
)
def test_parse_process_date_warns_once_on_invalid_value(value: str) -> None:
    warnings: list[str] = []

    assert _parse_process_date(value, "dataAjuizamento", warnings) is None
    assert warnings == ["dataAjuizamento inválido"]


def test_movement_values_without_movements() -> None:
    assert _movement_values({}) == ([], [])
    assert _movement_values({"movimentos": None}) == ([], [])
    assert _movement_values({"movimentos": []}) == ([], [])


def test_movement_values_rejects_non_list() -> None:
    assert _movement_values({"movimentos": {"codigo": 1}}) == (
        [],
        ["movimentos não é uma lista"],
    )


def test_movement_values_maps_fields() -> None:
    raw = {
        "codigo": 246,
        "nome": " Definitivo ",
        "dataHora": "2026-03-10T14:30:00Z",
        "orgaoJulgador": {"codigo": 1234, "nome": "1ª Vara Cível"},
        "complementosTabelados": [{"codigo": 1, "nome": "tipo"}],
    }

    values, warnings = _movement_values({"movimentos": [raw]})

    assert warnings == []
    assert values == [
        {
            "source_hash": _canonical_hash(raw),
            "codigo": 246,
            "nome": "Definitivo",
            "data_hora": datetime(2026, 3, 10, 14, 30, tzinfo=UTC),
            "orgao_julgador_codigo": "1234",
            "orgao_julgador_nome": "1ª Vara Cível",
            "complementos_tabelados": [{"codigo": 1, "nome": "tipo"}],
        }
    ]


def test_movement_values_skips_duplicates_and_invalid_items() -> None:
    first = {"codigo": 26, "nome": "Distribuição", "dataHora": "2026-03-01T10:00:00Z"}
    payload = {
        "movimentos": [
            first,
            dict(reversed(list(first.items()))),
            "invalido",
            {"codigo": 51, "nome": "Conclusão", "dataHora": "ontem"},
        ]
    }

    values, warnings = _movement_values(payload)

    assert [value["codigo"] for value in values] == [26, 51]
    assert values[1]["data_hora"] is None
    assert values[1]["orgao_julgador_codigo"] is None
    assert values[1]["complementos_tabelados"] is None
    assert warnings == [
        "movimento 2 inválido foi ignorado",
        "movimento 3.dataHora inválido",
    ]


def test_subject_values_without_subjects() -> None:
    assert _subject_values({}) == ([], [])
    assert _subject_values({"assuntos": []}) == ([], [])


def test_subject_values_rejects_non_list() -> None:
    assert _subject_values({"assuntos": "10433"}) == ([], ["assuntos não é uma lista"])


def test_subject_values_accepts_only_boolean_principal() -> None:
    values, _ = _subject_values(
        {
            "assuntos": [
                {"codigo": 1, "nome": "A", "principal": False},
                {"codigo": 2, "nome": "B", "principal": "true"},
                {"codigo": "x", "nome": "  "},
            ]
        }
    )

    assert values[0]["principal"] is False
    assert values[1]["principal"] is None
    assert values[2]["codigo"] is None
    assert values[2]["nome"] is None


def test_process_values_maps_datajud_payload() -> None:
    extract = _extract(
        {
            "numeroProcesso": "00000010220268260100",
            "grau": "G1",
            "classe": {"codigo": 7, "nome": "Procedimento Comum Cível"},
            "orgaoJulgador": {
                "codigo": 1234,
                "nome": "1ª Vara Cível",
                "codigoMunicipioIBGE": 3550308,
            },
            "formato": {"codigo": 1, "nome": "Eletrônico"},
            "sistema": {"codigo": "3", "nome": "SAJ"},
            "nivelSigilo": 0,
            "dataAjuizamento": "20260301120000",
            "dataHoraUltimaAtualizacao": "2026-03-05T09:00:00.000Z",
        }
    )
    before = datetime.now(UTC)

    values, warnings = _process_values(extract)

    assert warnings == []
    transformed_at = values.pop("transformed_at")
    assert before <= transformed_at <= datetime.now(UTC)
    assert values == {
        "bronze_extract_id": extract.id,
        "tribunal_sigla": "TJSP",
        "datajud_id": "TJSP_JE_00000001020268260100",
        "numero_processo": "00000010220268260100",
        "grau": "G1",
        "classe_codigo": 7,
        "classe_nome": "Procedimento Comum Cível",
        "orgao_julgador_codigo": "1234",
        "orgao_julgador_nome": "1ª Vara Cível",
        "orgao_julgador_municipio_ibge": "3550308",
        "formato_codigo": 1,
        "formato_nome": "Eletrônico",
        "sistema_codigo": 3,
        "sistema_nome": "SAJ",
        "nivel_sigilo": 0,
        "data_ajuizamento": date(2026, 3, 1),
        "data_hora_ultima_atualizacao": datetime(2026, 3, 5, 9, 0, tzinfo=UTC),
        "source_file": "raw/tjsp/2026/03/01/page-1.json.gz",
        "source_payload_hash": "a" * 64,
        "source_extracted_at": datetime(2026, 3, 2, 8, 0, tzinfo=UTC),
    }


def test_process_values_tolerates_missing_and_malformed_fields() -> None:
    extract = _extract(
        {
            "classe": "Procedimento Comum",
            "orgaoJulgador": None,
            "nivelSigilo": True,
            "dataAjuizamento": "20261301",
            "dataHoraUltimaAtualizacao": "ontem",
        }
    )

    values, warnings = _process_values(extract)

    assert warnings == [
        "dataAjuizamento inválido",
        "dataHoraUltimaAtualizacao inválido",
    ]
    for field in (
        "numero_processo",
        "grau",
        "classe_codigo",
        "classe_nome",
        "orgao_julgador_codigo",
        "orgao_julgador_nome",
        "orgao_julgador_municipio_ibge",
        "formato_codigo",
        "sistema_codigo",
        "nivel_sigilo",
        "data_ajuizamento",
        "data_hora_ultima_atualizacao",
    ):
        assert values[field] is None, field
    assert values["datajud_id"] == "TJSP_JE_00000001020268260100"
