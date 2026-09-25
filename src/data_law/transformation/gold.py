"""Gold materialization framework."""

import argparse
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

import polars as pl
from pglast import ast, parse_sql
from pglast.error import Error as PgLastError
from pglast.visitors import Visitor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from data_law.infra.database.settings import DatabaseSettings

if __name__ == "__main__":
    sys.modules["data_law.transformation.gold"] = sys.modules[__name__]

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_GOLD_SCHEMA = "gold"
_SILVER_SCHEMA = "silver"


class GoldConfigurationError(ValueError):
    """Invalid or unsafe Gold recipe."""


class GoldExecutionError(RuntimeError):
    """Gold recipe could not be completed."""


class GoldEngine(StrEnum):
    SQL = "sql"
    POLARS = "polars"


class GoldRefreshMode(StrEnum):
    REBUILD = "rebuild"


GoldTransform = Callable[["GoldContext"], pl.DataFrame | pl.LazyFrame]


@dataclass(frozen=True)
class GoldMaterialization:
    name: str
    engine: GoldEngine
    refresh_mode: GoldRefreshMode = GoldRefreshMode.REBUILD
    query: str | None = None
    transform: GoldTransform | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "nome da materializacao")
        if self.refresh_mode is not GoldRefreshMode.REBUILD:
            raise GoldConfigurationError("somente refresh rebuild e suportado")
        if self.engine is GoldEngine.SQL:
            if not self.query or self.transform:
                raise GoldConfigurationError("recipe SQL requer somente uma query")
            _validate_silver_select(self.query)
        elif self.engine is GoldEngine.POLARS:
            if self.query or not self.transform:
                raise GoldConfigurationError(
                    "recipe Polars requer somente um transform"
                )
        else:
            raise GoldConfigurationError(f"engine Gold desconhecida: {self.engine}")


@dataclass(frozen=True)
class GoldMaterializationResult:
    name: str
    rows: int


@dataclass(frozen=True)
class GoldRunReport:
    materializations: tuple[GoldMaterializationResult, ...]

    @property
    def count(self) -> int:
        return len(self.materializations)


class GoldRegistry:
    """Versioned, in-memory definitions consumed by the manual CLI."""

    def __init__(self, recipes: Iterable[GoldMaterialization] = ()) -> None:
        self._recipes: dict[str, GoldMaterialization] = {}
        for recipe in recipes:
            self.register(recipe)

    def register(self, recipe: GoldMaterialization) -> GoldMaterialization:
        if recipe.name in self._recipes:
            raise GoldConfigurationError(f"materializacao duplicada: {recipe.name}")
        self._recipes[recipe.name] = recipe
        return recipe

    def register_sql(self, name: str, query: str) -> GoldMaterialization:
        return self.register(GoldMaterialization(name, GoldEngine.SQL, query=query))

    def register_polars(
        self, name: str, transform: GoldTransform
    ) -> GoldMaterialization:
        return self.register(
            GoldMaterialization(name, GoldEngine.POLARS, transform=transform)
        )

    def select(self, name: str | None = None) -> tuple[GoldMaterialization, ...]:
        if name is None:
            return tuple(self._recipes.values())
        if name not in self._recipes:
            raise GoldConfigurationError(f"materializacao nao encontrada: {name}")
        return (self._recipes[name],)


DEFAULT_GOLD_REGISTRY = GoldRegistry()


def register_sql(name: str, query: str) -> GoldMaterialization:
    return DEFAULT_GOLD_REGISTRY.register_sql(name, query)


def register_polars(name: str, transform: GoldTransform) -> GoldMaterialization:
    return DEFAULT_GOLD_REGISTRY.register_polars(name, transform)


@dataclass(frozen=True)
class GoldContext:
    connection: Connection

    def read_silver(self, query: str) -> pl.DataFrame:
        _validate_silver_select(query)
        return pl.read_database(query=query, connection=self.connection)


class GoldMaterializer:
    """Atomically rebuild registered Gold tables."""

    def __init__(
        self, registry: GoldRegistry | None = None, engine: Engine | None = None
    ) -> None:
        self.registry = registry or DEFAULT_GOLD_REGISTRY
        self.engine = engine or create_engine(
            DatabaseSettings().database_url  # type: ignore[call-arg]
        )

    def run(self, name: str | None = None) -> GoldRunReport:
        results = []
        for recipe in self.registry.select(name):
            with self.engine.begin() as connection:
                rows = self._materialize(connection, recipe)
            results.append(GoldMaterializationResult(recipe.name, rows))
        return GoldRunReport(tuple(results))

    def _materialize(self, connection: Connection, recipe: GoldMaterialization) -> int:
        staging = _temporary_name("stg")
        if recipe.engine is GoldEngine.SQL:
            assert recipe.query is not None
            connection.execute(
                text(f"CREATE TABLE {_qualified_name(staging)} AS {recipe.query}")
            )
        else:
            assert recipe.transform is not None
            frame = recipe.transform(GoldContext(connection))
            if isinstance(frame, pl.LazyFrame):
                frame = frame.collect()
            if not isinstance(frame, pl.DataFrame):
                raise GoldExecutionError(
                    "transform deve retornar DataFrame ou LazyFrame"
                )
            _validate_frame(frame)
            frame.write_database(
                table_name=_qualified_name(staging),
                connection=connection,
                if_table_exists="fail",
                engine="sqlalchemy",
            )

        rows = connection.scalar(
            text(f"SELECT count(*) FROM {_qualified_name(staging)}")
        )
        assert isinstance(rows, int)
        self._replace_table(connection, staging, recipe.name)
        return rows

    def _replace_table(self, connection: Connection, staging: str, target: str) -> None:
        backup = _temporary_name("old")
        exists = connection.scalar(
            text("SELECT to_regclass(:name) IS NOT NULL"),
            {"name": f"{_GOLD_SCHEMA}.{target}"},
        )
        if exists:
            connection.execute(
                text(
                    f"ALTER TABLE {_qualified_name(target)} "
                    f"RENAME TO {_quote_identifier(backup)}"
                )
            )
        connection.execute(
            text(
                f"ALTER TABLE {_qualified_name(staging)} "
                f"RENAME TO {_quote_identifier(target)}"
            )
        )
        if exists:
            connection.execute(text(f"DROP TABLE {_qualified_name(backup)}"))


def _validate_silver_select(query: str) -> None:
    if not query or not query.strip():
        raise GoldConfigurationError("query SQL nao pode estar vazia")
    try:
        statements = parse_sql(query)
    except PgLastError as error:
        raise GoldConfigurationError(f"query SQL invalida: {error}") from error
    if len(statements) != 1 or not isinstance(statements[0].stmt, ast.SelectStmt):
        raise GoldConfigurationError("recipe SQL deve conter exatamente um SELECT")

    statement = statements[0].stmt
    with_clause = statement.withClause
    if with_clause is None or with_clause.ctes is None:
        ctes: set[str] = set()
    else:
        ctes = {cte.ctename for cte in with_clause.ctes}
    _SilverSelectVisitor(ctes)(statement)


class _SilverSelectVisitor(Visitor):
    def __init__(self, ctes: set[str]) -> None:
        super().__init__()
        self.ctes = ctes

    def visit_RangeVar(self, ancestors, node) -> None:
        if node.schemaname == _SILVER_SCHEMA:
            return
        if node.schemaname is None and node.relname in self.ctes:
            return
        raise GoldConfigurationError(
            "recipes Gold so podem ler tabelas qualificadas do schema silver"
        )

    def visit_RangeFunction(self, ancestors, node) -> None:
        raise GoldConfigurationError("funcoes nao podem ser fonte de dados Gold")

    def visit_InsertStmt(self, ancestors, node) -> None:
        raise GoldConfigurationError("recipes Gold nao podem modificar dados")

    def visit_UpdateStmt(self, ancestors, node) -> None:
        raise GoldConfigurationError("recipes Gold nao podem modificar dados")

    def visit_DeleteStmt(self, ancestors, node) -> None:
        raise GoldConfigurationError("recipes Gold nao podem modificar dados")

    def visit_MergeStmt(self, ancestors, node) -> None:
        raise GoldConfigurationError("recipes Gold nao podem modificar dados")


def _validate_frame(frame: pl.DataFrame) -> None:
    if not frame.columns:
        raise GoldExecutionError("tabela Gold precisa ter ao menos uma coluna")
    if len(set(frame.columns)) != len(frame.columns):
        raise GoldExecutionError("tabela Gold nao pode ter colunas duplicadas")
    for column in frame.columns:
        _validate_identifier(column, "nome da coluna")


def _validate_identifier(value: str, label: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise GoldConfigurationError(
            f"{label} deve conter apenas minusculas, numeros ou underscore"
        )


def _quote_identifier(value: str) -> str:
    _validate_identifier(value, "identificador")
    return f'"{value}"'


def _qualified_name(table_name: str) -> str:
    return f"{_quote_identifier(_GOLD_SCHEMA)}.{_quote_identifier(table_name)}"


def _temporary_name(kind: str) -> str:
    return f"gold_{kind}_{uuid4().hex}"


def main(argv: Sequence[str] | None = None) -> None:
    """Run recipes registered in data_law.transformation.gold_recipes."""
    from data_law.transformation import gold_recipes  # noqa: F401

    parser = argparse.ArgumentParser(description="Materializa a camada Gold")
    parser.add_argument("--name", help="nome da materializacao Gold")
    arguments = parser.parse_args(argv)
    report = GoldMaterializer().run(arguments.name)
    print(f"Gold materializada: {report.count} tabela(s).")
    for result in report.materializations:
        print(f"- {result.name}: {result.rows} linha(s)")


if __name__ == "__main__":
    main()
