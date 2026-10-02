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
