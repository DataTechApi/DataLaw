"""Integration tests for the Adherence Index and party view Gold recipes.

They seed an isolated tribunal (``PYTEST``) in a disposable PostgreSQL database,
rebuild the Gold tables and remove the seeded rows afterwards. Never point
DATABASE_URL at production: these tests write and rebuild tables.
"""

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, create_engine, text

from data_law.transformation import gold_recipes  # noqa: F401
from data_law.transformation.gold import GoldMaterializer

TRIBUNAL = "PYTEST"
ASSUNTO_CODIGO = 999_001
ASSUNTO_NOME = "Assunto de teste de adesão"
ORGAO = "1ª Vara de Teste"
MOVEMENT_NAMES = {
    246: "Arquivamento definitivo",
    219: "Procedência",
    220: "Improcedência",
    221: "Procedência em Parte",
}
CLOSED_AT = datetime(2026, 6, 1, tzinfo=UTC)

pytestmark = pytest.mark.integration


@pytest.fixture
def engine() -> Iterator[Engine]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL não configurada para teste de integração")
    engine = create_engine(database_url)
    _cleanup(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        for name in (
            "topic_adherence",
            "topic_adherence_evidence",
            "topic_party_results",
        ):
            GoldMaterializer(engine=engine).run(name)
        engine.dispose()


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM silver.jurisprudencia WHERE tribunal_sigla = :t"),
            {"t": TRIBUNAL},
        )
        connection.execute(
            text("DELETE FROM bronze.datajud_extract WHERE tribunal_sigla = :t"),
            {"t": TRIBUNAL},
        )


def _seed_case(
    engine: Engine,
    merit_code: int | None,
    nivel_sigilo: int = 0,
) -> None:
    extract_id = uuid.uuid4()
    process_id = uuid.uuid4()
    datajud_id = f"pytest-{process_id}"
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO bronze.datajud_extract (
                    id, tribunal_alias, tribunal_sigla, datajud_id, source_file,
                    extracted_at, payload_hash, payload
                ) VALUES (
                    :id, 'api_publica_pytest', :t, :datajud_id, 'pytest',
                    now(), :hash, '{}'::jsonb
                )
                """
            ),
            {
                "id": extract_id,
                "t": TRIBUNAL,
                "datajud_id": datajud_id,
                "hash": uuid.uuid4().hex + uuid.uuid4().hex,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO silver.processo (
                    id, bronze_extract_id, tribunal_sigla, datajud_id,
                    numero_processo, orgao_julgador_nome, nivel_sigilo,
                    source_file, source_payload_hash, source_extracted_at,
                    transformed_at
                ) VALUES (
                    :id, :extract_id, :t, :datajud_id, :numero, :orgao, :sigilo,
                    'pytest', :hash, now(), now()
                )
                """
            ),
            {
                "id": process_id,
                "extract_id": extract_id,
                "t": TRIBUNAL,
                "datajud_id": datajud_id,
                "numero": process_id.hex[:20],
                "orgao": ORGAO,
                "sigilo": nivel_sigilo,
                "hash": uuid.uuid4().hex + uuid.uuid4().hex,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO silver.processo_assunto (
                    id, processo_id, source_hash, codigo, nome
                ) VALUES (:id, :processo_id, :hash, :codigo, :nome)
                """
            ),
            {
                "id": uuid.uuid4(),
                "processo_id": process_id,
                "hash": uuid.uuid4().hex + uuid.uuid4().hex,
                "codigo": ASSUNTO_CODIGO,
                "nome": ASSUNTO_NOME,
            },
        )
        movements = [(246, CLOSED_AT)]
        if merit_code is not None:
            movements.append((merit_code, CLOSED_AT - timedelta(days=30)))
        for code, moment in movements:
            connection.execute(
                text(
                    """
                    INSERT INTO silver.movimento (
                        id, processo_id, source_hash, codigo, nome, data_hora
                    ) VALUES (:id, :processo_id, :hash, :codigo, :nome, :data_hora)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "processo_id": process_id,
                    "hash": uuid.uuid4().hex + uuid.uuid4().hex,
                    "codigo": code,
                    "nome": MOVEMENT_NAMES[code],
                    "data_hora": moment,
                },
            )


def _seed_precedent(engine: Engine, identifier: str, direction: str | None) -> None:
    precedent_id = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO silver.jurisprudencia (
                    id, tribunal_sigla, identificador_precedente, titulo, ementa,
                    assunto_codigo, assunto_nome, source_hash
                ) VALUES (
                    :id, :t, :ident, :ident, 'Ementa de teste', :codigo, :nome, :hash
                )
                """
            ),
            {
                "id": precedent_id,
                "t": TRIBUNAL,
                "ident": identifier,
                "codigo": ASSUNTO_CODIGO,
                "nome": ASSUNTO_NOME,
                "hash": uuid.uuid4().hex + uuid.uuid4().hex,
            },
        )
        if direction is not None:
            connection.execute(
                text(
                    """
                    INSERT INTO silver.precedente_direcao (
                        id, jurisprudencia_id, direcao, curador
                    ) VALUES (:id, :jurisprudencia_id, :direcao, 'pytest')
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "jurisprudencia_id": precedent_id,
                    "direcao": direction,
                },
            )


def _seed_scenario(engine: Engine) -> None:
    """6 × 219, 2 × 221, 2 × 220, one case without merit and one confidential."""
    for code in [219] * 6 + [221] * 2 + [220] * 2:
        _seed_case(engine, code)
    _seed_case(engine, None)
    _seed_case(engine, 219, nivel_sigilo=1)


def test_topic_party_results_splits_results_between_plaintiff_and_defendant(
    engine: Engine,
) -> None:
    _seed_scenario(engine)

    GoldMaterializer(engine=engine).run("topic_party_results")

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    "SELECT * FROM gold.topic_party_results WHERE tribunal_sigla = :t"
                ),
                {"t": TRIBUNAL},
            )
            .mappings()
            .one()
        )

    assert row["processos_encerrados"] == 11
    assert row["decisoes_com_resultado"] == 10
    assert (row["procedentes"], row["parciais"], row["improcedentes"]) == (6, 2, 2)
    assert float(row["autor_pct"]) == 70.0
    assert float(row["reu_pct"]) == 30.0


def test_topic_adherence_classifies_by_thesis_direction(engine: Engine) -> None:
    _seed_scenario(engine)
    _seed_precedent(engine, "Tese a favor do autor", "autor")
    _seed_precedent(engine, "Tese a favor do réu", "reu")
    _seed_precedent(engine, "Tese indefinida", "indefinida")
    _seed_precedent(engine, "Tese sem curadoria", None)

    GoldMaterializer(engine=engine).run("topic_adherence")

    with engine.connect() as connection:
        rows = {
            row["identificador_precedente"]: row
            for row in connection.execute(
                text("SELECT * FROM gold.topic_adherence WHERE tribunal_sigla = :t"),
                {"t": TRIBUNAL},
            ).mappings()
        }

    assert set(rows) == {"Tese a favor do autor", "Tese a favor do réu"}

    autor = rows["Tese a favor do autor"]
    assert autor["orgao_julgador_nome"] == ORGAO
    assert autor["processos_encerrados"] == 11
    assert autor["decisoes_com_resultado"] == 10
    assert (autor["aderentes"], autor["parciais"], autor["nao_aderentes"]) == (6, 2, 2)
    assert float(autor["indice_adesao_pct"]) == 70.0

    reu = rows["Tese a favor do réu"]
    assert (reu["aderentes"], reu["parciais"], reu["nao_aderentes"]) == (2, 2, 6)
    assert float(reu["indice_adesao_pct"]) == 30.0


def test_topic_adherence_is_null_without_decisions_with_a_result(
    engine: Engine,
) -> None:
    _seed_case(engine, None)
    _seed_precedent(engine, "Tese a favor do autor", "autor")

    GoldMaterializer(engine=engine).run("topic_adherence")

    with engine.connect() as connection:
        row = (
            connection.execute(
                text("SELECT * FROM gold.topic_adherence WHERE tribunal_sigla = :t"),
                {"t": TRIBUNAL},
            )
            .mappings()
            .one()
        )

    assert row["decisoes_com_resultado"] == 0
    assert row["indice_adesao_pct"] is None


def test_topic_adherence_evidence_matches_the_index(engine: Engine) -> None:
    _seed_scenario(engine)
    _seed_precedent(engine, "Tese a favor do autor", "autor")
    _seed_precedent(engine, "Tese sem curadoria", None)

    GoldMaterializer(engine=engine).run("topic_adherence")
    GoldMaterializer(engine=engine).run("topic_adherence_evidence")

    with engine.connect() as connection:
        index = (
            connection.execute(
                text("SELECT * FROM gold.topic_adherence WHERE tribunal_sigla = :t"),
                {"t": TRIBUNAL},
            )
            .mappings()
            .one()
        )
        evidence = (
            connection.execute(
                text(
                    "SELECT * FROM gold.topic_adherence_evidence "
                    "WHERE tribunal_sigla = :t"
                ),
                {"t": TRIBUNAL},
            )
            .mappings()
            .all()
        )

    assert {row["jurisprudencia_id"] for row in evidence} == {
        index["jurisprudencia_id"]
    }
    assert len(evidence) == index["decisoes_com_resultado"] == 10
    by_class = {
        name: sum(1 for row in evidence if row["classificacao"] == name)
        for name in ("aderente", "parcial", "nao_aderente")
    }
    assert by_class == {
        "aderente": index["aderentes"],
        "parcial": index["parciais"],
        "nao_aderente": index["nao_aderentes"],
    }
    assert {row["movimento_nome"] for row in evidence} >= {"Procedência"}
    assert all(row["numero_processo"] for row in evidence)
    assert all(row["data_julgamento"] for row in evidence)
