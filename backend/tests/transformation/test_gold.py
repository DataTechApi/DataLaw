import polars as pl
import pytest

from data_law.transformation.gold import (
    DEFAULT_GOLD_REGISTRY,
    GoldConfigurationError,
    GoldEngine,
    GoldExecutionError,
    GoldRegistry,
    _validate_frame,
)
from data_law.transformation.silver import _canonical_hash, _subject_values


def test_registry_registers_sql_and_polars_recipes() -> None:
    registry = GoldRegistry()
    sql_recipe = registry.register_sql(
        "processos_por_classe",
        "SELECT classe_nome, count(*) AS total "
        "FROM silver.processo GROUP BY classe_nome",
    )

    def transform(_: object) -> pl.DataFrame:
        return pl.DataFrame({"classe_nome": ["Civil"], "total": [1]})

    polars_recipe = registry.register_polars("classes_polars", transform)  # type: ignore[arg-type]

    assert [recipe.name for recipe in registry.select()] == [
        sql_recipe.name,
        polars_recipe.name,
    ]
    assert registry.select("classes_polars") == (polars_recipe,)


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM silver.processo",
        "SELECT * FROM bronze.datajud_extract",
        "SELECT * FROM processo",
        "WITH removidos AS (DELETE FROM silver.processo RETURNING id) "
        "SELECT * FROM removidos",
        "SELECT * FROM generate_series(1, 2)",
    ],
)
def test_registry_rejects_non_readonly_or_non_silver_sql(query: str) -> None:
    with pytest.raises(GoldConfigurationError):
        GoldRegistry().register_sql("invalida", query)


def test_registry_accepts_readonly_cte_from_silver() -> None:
    recipe = GoldRegistry().register_sql(
        "processos_cte",
        "WITH processos AS (SELECT id FROM silver.processo) SELECT id FROM processos",
    )

    assert recipe.name == "processos_cte"


def test_success_by_class_recipe_is_registered() -> None:
    from data_law.transformation import gold_recipes  # noqa: F401

    recipe = DEFAULT_GOLD_REGISTRY.select("process_results")[0]

    assert recipe.engine is GoldEngine.SQL
    assert recipe.query is not None
    assert "silver.processo" in recipe.query
    assert "silver.movimento" in recipe.query
    assert "sem_resultado_de_merito" in recipe.query


def test_success_by_topic_recipe_is_registered() -> None:
    from data_law.transformation import gold_recipes  # noqa: F401

    recipe = DEFAULT_GOLD_REGISTRY.select("topic_results")[0]

    assert recipe.engine is GoldEngine.SQL
    assert recipe.query is not None
    assert "silver.processo" in recipe.query
    assert "silver.processo_assunto" in recipe.query
    assert "silver.movimento" in recipe.query
    assert "assunto_codigo" in recipe.query
    assert "assunto_nome" in recipe.query
    assert "taxa_sucesso_ponderada_pct" in recipe.query


def test_subject_extraction_and_canonical_hashing() -> None:
    payload = {
        "assuntos": [
            {"codigo": 10433, "nome": "Indenização por Dano Moral", "principal": True},
            {"codigo": 10433, "nome": "Indenização por Dano Moral", "principal": True},
            {"codigo": "7779", "nome": "Responsabilidade Civil"},
            "invalido",
        ]
    }
    values, warnings = _subject_values(payload)

    assert len(values) == 2
    assert len(warnings) == 1
    assert "assunto 3 inválido" in warnings[0]

    assert values[0]["codigo"] == 10433
    assert values[0]["nome"] == "Indenização por Dano Moral"
    assert values[0]["principal"] is True
    assert values[0]["source_hash"] == _canonical_hash(
        {"codigo": 10433, "nome": "Indenização por Dano Moral", "principal": True}
    )

    assert values[1]["codigo"] == 7779
    assert values[1]["nome"] == "Responsabilidade Civil"
    assert values[1]["principal"] is None


def test_registry_rejects_duplicate_and_missing_names() -> None:
    registry = GoldRegistry()
    registry.register_sql("processos", "SELECT id FROM silver.processo")

    with pytest.raises(GoldConfigurationError, match="duplicada"):
        registry.register_sql("processos", "SELECT id FROM silver.processo")
    with pytest.raises(GoldConfigurationError, match="nao encontrada"):
        registry.select("ausente")


def test_polars_output_requires_valid_nonempty_columns() -> None:
    with pytest.raises(GoldExecutionError, match="ao menos uma coluna"):
        _validate_frame(pl.DataFrame())

    with pytest.raises(GoldConfigurationError, match="nome da coluna"):
        _validate_frame(pl.DataFrame({"Classe Nome": ["Civil"]}))
