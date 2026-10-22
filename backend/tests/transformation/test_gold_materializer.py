import copy
import re
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import polars as pl
import pytest

from data_law.transformation import gold
from data_law.transformation.gold import (
    DEFAULT_GOLD_REGISTRY,
    GoldConfigurationError,
    GoldContext,
    GoldEngine,
    GoldExecutionError,
    GoldMaterialization,
    GoldMaterializationResult,
    GoldMaterializer,
    GoldRegistry,
    GoldRunReport,
    _qualified_name,
    _quote_identifier,
    _temporary_name,
)

_CREATE = re.compile(r'^CREATE TABLE "gold"\."(\w+)" AS (.+)$', re.DOTALL)
_COUNT = re.compile(r'^SELECT count\(\*\) FROM "gold"\."(\w+)"$')
_RENAME = re.compile(r'^ALTER TABLE "gold"\."(\w+)" RENAME TO "(\w+)"$')
_DROP = re.compile(r'^DROP TABLE "gold"\."(\w+)"$')
_TABLE_NAME = re.compile(r'^"gold"\."(\w+)"$')


class FakeEngine:
    """Keeps Gold tables as {name: row count} and rolls back failed transactions."""

    def __init__(self, tables: dict[str, int] | None = None) -> None:
        self.tables = dict(tables or {})
        self.query_rows: dict[str, int] = {}
        self.statements: list[str] = []
        self.transactions = 0

    @contextmanager
    def begin(self):
        self.transactions += 1
        snapshot = copy.deepcopy(self.tables)
        try:
            yield FakeConnection(self)
        except Exception:
            self.tables = snapshot
            raise


class FakeConnection:
    def __init__(self, engine: FakeEngine) -> None:
        self.engine = engine

    def execute(self, statement: Any) -> None:
        sql = str(statement)
        self.engine.statements.append(sql)
        tables = self.engine.tables
        if match := _CREATE.match(sql):
            name, query = match.groups()
            assert name not in tables
            tables[name] = self.engine.query_rows.get(query, 0)
        elif match := _RENAME.match(sql):
            source, target = match.groups()
            assert target not in tables
            tables[target] = tables.pop(source)
        elif match := _DROP.match(sql):
            del tables[match.group(1)]
        else:
            raise AssertionError(f"SQL inesperado: {sql}")

    def scalar(self, statement: Any, params: dict[str, Any] | None = None) -> Any:
        sql = str(statement)
        self.engine.statements.append(sql)
        if match := _COUNT.match(sql):
            return self.engine.tables[match.group(1)]
        if "to_regclass" in sql:
            assert params is not None
            schema, name = params["name"].split(".")
            assert schema == "gold"
            return name in self.engine.tables
        raise AssertionError(f"SQL inesperado: {sql}")


@pytest.fixture
def written_frames(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace DataFrame.write_database with a fake that writes to FakeEngine."""
    calls: list[dict[str, Any]] = []

    def fake_write_database(
        self: pl.DataFrame, table_name: str, connection: Any, **kwargs: Any
    ) -> int:
        match = _TABLE_NAME.match(table_name)
        assert match is not None, table_name
        calls.append({"table": match.group(1), "frame": self, **kwargs})
        connection.engine.tables[match.group(1)] = self.height
        return self.height

    monkeypatch.setattr(pl.DataFrame, "write_database", fake_write_database)
    return calls


def _gold_tables(engine: FakeEngine) -> dict[str, int]:
    return {
        name: rows
        for name, rows in engine.tables.items()
        if not name.startswith("gold_")
    }


QUERY = "SELECT classe_nome, count(*) AS total FROM silver.processo GROUP BY 1"


def test_sql_recipe_creates_new_table_from_staging() -> None:
    registry = GoldRegistry()
    registry.register_sql("processos_por_classe", QUERY)
    engine = FakeEngine()
    engine.query_rows[QUERY] = 12

    report = GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert report == GoldRunReport(
        (GoldMaterializationResult("processos_por_classe", 12),)
    )
    assert report.count == 1
    assert engine.tables == {"processos_por_classe": 12}
    assert engine.statements[0].startswith('CREATE TABLE "gold"."gold_stg_')
    assert engine.statements[0].endswith(f" AS {QUERY}")
    assert not any(sql.startswith("DROP") for sql in engine.statements)


def test_sql_recipe_swaps_existing_table_and_drops_old_copy() -> None:
    registry = GoldRegistry()
    registry.register_sql("processos_por_classe", QUERY)
    engine = FakeEngine({"processos_por_classe": 5, "outra_tabela": 7})
    engine.query_rows[QUERY] = 12

    GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert engine.tables == {"processos_por_classe": 12, "outra_tabela": 7}
    operations = [sql.split(" ")[0] for sql in engine.statements]
    assert operations == ["CREATE", "SELECT", "SELECT", "ALTER", "ALTER", "DROP"]
    backup_rename, staging_rename, drop = engine.statements[3:]
    assert backup_rename.startswith(
        'ALTER TABLE "gold"."processos_por_classe" RENAME TO "gold_old_'
    )
    assert staging_rename.endswith('RENAME TO "processos_por_classe"')
    assert drop.startswith('DROP TABLE "gold"."gold_old_')


def test_each_recipe_runs_in_its_own_transaction() -> None:
    registry = GoldRegistry()
    registry.register_sql("primeira", "SELECT id FROM silver.processo")
    registry.register_sql("segunda", "SELECT id FROM silver.movimento")
    engine = FakeEngine()

    report = GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert [result.name for result in report.materializations] == [
        "primeira",
        "segunda",
    ]
    assert engine.transactions == 2
    assert set(engine.tables) == {"primeira", "segunda"}


def test_run_by_name_only_materializes_selected_recipe() -> None:
    registry = GoldRegistry()
    registry.register_sql("primeira", "SELECT id FROM silver.processo")
    registry.register_sql("segunda", "SELECT id FROM silver.movimento")
    engine = FakeEngine()

    report = GoldMaterializer(registry, engine).run("segunda")  # type: ignore[arg-type]

    assert [result.name for result in report.materializations] == ["segunda"]
    assert set(engine.tables) == {"segunda"}


def test_run_with_unknown_name_fails_before_touching_database() -> None:
    engine = FakeEngine()

    with pytest.raises(GoldConfigurationError, match="nao encontrada"):
        GoldMaterializer(GoldRegistry(), engine).run("ausente")  # type: ignore[arg-type]

    assert engine.transactions == 0


def test_failed_recipe_keeps_previous_table_and_earlier_results(
    written_frames: list[dict[str, Any]],
) -> None:
    def broken(context: GoldContext) -> pl.DataFrame:
        raise RuntimeError("falha no transform")

    registry = GoldRegistry()
    registry.register_sql("primeira", "SELECT id FROM silver.processo")
    registry.register_polars("quebrada", broken)
    engine = FakeEngine({"primeira": 1, "quebrada": 9})
    engine.query_rows["SELECT id FROM silver.processo"] = 3

    with pytest.raises(RuntimeError, match="falha no transform"):
        GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert engine.tables == {"primeira": 3, "quebrada": 9}


def test_polars_recipe_writes_dataframe_to_staging(
    written_frames: list[dict[str, Any]],
) -> None:
    def transform(context: GoldContext) -> pl.DataFrame:
        return pl.DataFrame({"classe_nome": ["Cível", "Criminal"], "total": [3, 1]})

    registry = GoldRegistry()
    registry.register_polars("classes", transform)
    engine = FakeEngine({"classes": 10})

    report = GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert report.materializations == (GoldMaterializationResult("classes", 2),)
    assert engine.tables == {"classes": 2}
    [call] = written_frames
    assert call["table"].startswith("gold_stg_")
    assert call["if_table_exists"] == "fail"
    assert call["engine"] == "sqlalchemy"
    assert call["frame"].columns == ["classe_nome", "total"]


def test_polars_recipe_accepts_lazy_frame(
    written_frames: list[dict[str, Any]],
) -> None:
    def transform(context: GoldContext) -> pl.LazyFrame:
        return pl.LazyFrame({"total": [1, 2, 3]}).filter(pl.col("total") > 1)

    registry = GoldRegistry()
    registry.register_polars("totais", transform)
    engine = FakeEngine()

    report = GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert report.materializations == (GoldMaterializationResult("totais", 2),)
    assert isinstance(written_frames[0]["frame"], pl.DataFrame)


@pytest.mark.parametrize("result", [None, [{"total": 1}], {"total": [1]}])
def test_polars_recipe_must_return_a_frame(
    result: object, written_frames: list[dict[str, Any]]
) -> None:
    registry = GoldRegistry()
    registry.register_polars("invalida", lambda context: result)  # type: ignore[arg-type,return-value]
    engine = FakeEngine()

    with pytest.raises(GoldExecutionError, match="DataFrame ou LazyFrame"):
        GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert written_frames == []
    assert engine.tables == {}


@pytest.mark.parametrize(
    ("frame", "error"),
    [
        (pl.DataFrame(), "ao menos uma coluna"),
        (pl.DataFrame({"Total": [1]}), "nome da coluna"),
        (pl.DataFrame({"total processos": [1]}), "nome da coluna"),
    ],
)
def test_polars_recipe_with_invalid_columns_writes_nothing(
    frame: pl.DataFrame, error: str, written_frames: list[dict[str, Any]]
) -> None:
    registry = GoldRegistry()
    registry.register_polars("invalida", lambda context: frame)
    engine = FakeEngine({"invalida": 4})

    with pytest.raises((GoldExecutionError, GoldConfigurationError), match=error):
        GoldMaterializer(registry, engine).run()  # type: ignore[arg-type]

    assert written_frames == []
    assert engine.tables == {"invalida": 4}


def test_polars_frame_with_duplicate_columns_is_rejected() -> None:
    # Polars nao permite construir um DataFrame com colunas duplicadas.
    frame: Any = SimpleNamespace(columns=["total", "total"])

    with pytest.raises(GoldExecutionError, match="duplicadas"):
        gold._validate_frame(frame)


def test_context_reads_silver_with_polars(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    expected = pl.DataFrame({"id": [1]})

    def fake_read_database(*, query: str, connection: object) -> pl.DataFrame:
        calls.append((query, connection))
        return expected

    monkeypatch.setattr(pl, "read_database", fake_read_database)
    connection = object()

    frame = GoldContext(connection).read_silver("SELECT id FROM silver.processo")  # type: ignore[arg-type]

    assert frame is expected
    assert calls == [("SELECT id FROM silver.processo", connection)]


def test_context_rejects_reading_outside_silver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(**kwargs: object) -> None:
        raise AssertionError("não deveria consultar o banco")

    monkeypatch.setattr(pl, "read_database", fail)

    with pytest.raises(GoldConfigurationError, match="schema silver"):
        GoldContext(object()).read_silver("SELECT * FROM bronze.datajud_extract")  # type: ignore[arg-type]


def test_materializer_uses_default_registry() -> None:
    materializer = GoldMaterializer(engine=FakeEngine())  # type: ignore[arg-type]

    assert materializer.registry is DEFAULT_GOLD_REGISTRY


def test_materializer_creates_engine_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/test")
    created: list[str] = []
    monkeypatch.setattr(gold, "create_engine", lambda url: created.append(url) or url)

    materializer = GoldMaterializer(GoldRegistry())

    assert created == ["postgresql+psycopg://u:p@localhost/test"]
    assert materializer.engine == created[0]


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"engine": GoldEngine.SQL, "refresh_mode": "incremental"}, "rebuild"),
        ({"engine": GoldEngine.SQL}, "somente uma query"),
        (
            {
                "engine": GoldEngine.SQL,
                "query": "SELECT id FROM silver.processo",
                "transform": lambda context: pl.DataFrame(),
            },
            "somente uma query",
        ),
        ({"engine": GoldEngine.POLARS}, "somente um transform"),
        (
            {
                "engine": GoldEngine.POLARS,
                "query": "SELECT id FROM silver.processo",
                "transform": lambda context: pl.DataFrame(),
            },
            "somente um transform",
        ),
        ({"engine": "spark"}, "engine Gold desconhecida"),
    ],
)
def test_materialization_rejects_invalid_configuration(
    kwargs: dict[str, Any], error: str
) -> None:
    with pytest.raises(GoldConfigurationError, match=error):
        GoldMaterialization("recipe", **kwargs)


@pytest.mark.parametrize(
    "name", ["Processos", "1processos", "processos-classe", "", "a" * 64]
)
def test_materialization_rejects_invalid_table_name(name: str) -> None:
    with pytest.raises(GoldConfigurationError, match="nome da materializacao"):
        GoldMaterialization(name, GoldEngine.SQL, query="SELECT 1")


@pytest.mark.parametrize(
    ("query", "error"),
    [
        ("", "requer somente uma query"),
        ("   ", "nao pode estar vazia"),
        ("SELEC id FROM silver.processo", "query SQL invalida"),
        (
            "SELECT id FROM silver.processo; SELECT id FROM silver.movimento",
            "exatamente um SELECT",
        ),
        ("UPDATE silver.processo SET grau = 'G2'", "exatamente um SELECT"),
        (
            "WITH novos AS (INSERT INTO silver.processo (id) VALUES (1) RETURNING id) "
            "SELECT id FROM novos",
            "nao podem modificar dados",
        ),
        (
            "WITH alterados AS (UPDATE silver.processo SET grau = 'G2' RETURNING id) "
            "SELECT id FROM alterados",
            "nao podem modificar dados",
        ),
        (
            "SELECT p.id FROM silver.processo p JOIN gold.processos g ON g.id = p.id",
            "schema silver",
        ),
        (
            "SELECT id FROM silver.processo "
            "WHERE id IN (SELECT processo_id FROM public.movimento)",
            "schema silver",
        ),
    ],
)
def test_sql_recipe_rejects_unsafe_or_invalid_query(query: str, error: str) -> None:
    with pytest.raises(GoldConfigurationError, match=error):
        GoldRegistry().register_sql("recipe", query)


def test_sql_recipe_accepts_query_without_tables() -> None:
    recipe = GoldRegistry().register_sql("constante", "SELECT 1 AS um")

    assert recipe.query == "SELECT 1 AS um"


def test_identifier_helpers_quote_and_validate() -> None:
    assert _quote_identifier("processos") == '"processos"'
    assert _qualified_name("processos") == '"gold"."processos"'
    with pytest.raises(GoldConfigurationError):
        _quote_identifier('processos"; DROP TABLE x; --')


def test_temporary_names_are_unique_valid_identifiers() -> None:
    names = {_temporary_name("stg") for _ in range(50)}

    assert len(names) == 50
    for name in names:
        assert name.startswith("gold_stg_")
        assert _quote_identifier(name) == f'"{name}"'


def test_main_runs_materializer_and_prints_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    names: list[str | None] = []

    class FakeMaterializer:
        def run(self, name: str | None = None) -> GoldRunReport:
            names.append(name)
            return GoldRunReport(
                (
                    GoldMaterializationResult("aderencia_por_tema", 42),
                    GoldMaterializationResult("precedentes_por_tema", 7),
                )
            )

    monkeypatch.setattr(gold, "GoldMaterializer", FakeMaterializer)

    gold.main(["--name", "aderencia_por_tema"])

    assert names == ["aderencia_por_tema"]
    assert capsys.readouterr().out.splitlines() == [
        "Gold materializada: 2 tabela(s).",
        "- aderencia_por_tema: 42 linha(s)",
        "- precedentes_por_tema: 7 linha(s)",
    ]


def test_main_without_name_runs_every_recipe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    names: list[str | None] = []

    class FakeMaterializer:
        def run(self, name: str | None = None) -> GoldRunReport:
            names.append(name)
            return GoldRunReport(())

    monkeypatch.setattr(gold, "GoldMaterializer", FakeMaterializer)

    gold.main([])

    assert names == [None]
    assert capsys.readouterr().out == "Gold materializada: 0 tabela(s).\n"
