"""Register project-specific Gold recipes here.

Example SQL:
    register_sql(
        "processos_por_classe",
        "SELECT classe_nome, count(*) AS total "
        "FROM silver.processo GROUP BY classe_nome",
    )

Example Polars:
    def processos(context: GoldContext) -> pl.LazyFrame:
        return context.read_silver("SELECT * FROM silver.processo").lazy()

    register_polars("processos", processos)
"""

from data_law.infra.database.model.gold import process_results  # noqa: F401
from data_law.transformation.gold import GoldContext, register_polars, register_sql

__all__ = ["GoldContext", "register_polars", "register_sql"]
