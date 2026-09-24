# Criacao de tabelas Gold

Este guia explica como adicionar tabelas analiticas ao schema PostgreSQL Gold.
Uma tabela Gold e declarada como uma recipe versionada e materializada a partir
da Silver. Nao crie manualmente tabelas no banco.

## Antes de criar uma recipe

Atualize o banco e confirme que a Silver esta atual:

~~~bash
uv run alembic upgrade head
uv run task silver-load
~~~

Adicione a definicao em
src/data_law/transformation/gold_recipes.py. O executor importa esse modulo
antes de executar as recipes registradas.

## Regras do contrato

- O nome da tabela deve usar somente letras minusculas, numeros e underscore,
  comecando por letra e com no maximo 63 caracteres. Por exemplo:
  processos_por_classe.
- As colunas de uma tabela criada por Polars seguem a mesma regra de nomes.
- A tabela destino e criada automaticamente no schema gold. Uma recipe chamada
  processos_por_classe cria gold.processos_por_classe.
- A versao atual usa somente rebuild completo. Nao ha atualizacao incremental.
- Uma recipe SQL deve conter exatamente um SELECT e ler apenas tabelas
  qualificadas do schema silver. CTEs de leitura sao permitidas.
- INSERT, UPDATE, DELETE, MERGE, DDL, tabelas de outros schemas e funcoes como
  fonte de dados sao rejeitados.

## Recipe SQL

Use SQL quando a transformacao puder ser feita no PostgreSQL. Importe
register_sql e registre uma consulta unica:

~~~python
from data_law.transformation.gold import register_sql

register_sql(
    "processos_por_classe",
    """
    SELECT
        tribunal_sigla,
        classe_nome,
        count(*) AS total_processos
    FROM silver.processo
    GROUP BY tribunal_sigla, classe_nome
    """,
)
~~~

A consulta nao deve incluir CREATE TABLE, INSERT ou ponto e virgula seguido de
outro comando. O executor cria uma tabela temporaria, grava o resultado e a
troca pela tabela destino dentro de uma transacao.

## Recipe Polars

Use Polars quando a logica precisar de operacoes DataFrame. A funcao recebe um
GoldContext e deve retornar um polars.DataFrame ou polars.LazyFrame.

~~~python
import polars as pl

from data_law.transformation.gold import GoldContext, register_polars


def processos_por_ano(context: GoldContext) -> pl.LazyFrame:
    processos = context.read_silver(
        """
        SELECT tribunal_sigla, data_ajuizamento
        FROM silver.processo
        """
    )
    return (
        processos.lazy()
        .with_columns(pl.col("data_ajuizamento").dt.year().alias("ano"))
        .group_by("tribunal_sigla", "ano")
        .len("total_processos")
    )


register_polars("processos_por_ano", processos_por_ano)
~~~

Use context.read_silver para carregar a origem. Ela aplica as mesmas regras de
seguranca do SQL: somente SELECT e apenas tabelas Silver qualificadas.

## Executar e conferir

Execute todas as recipes:

~~~bash
uv run task gold-load
~~~

Para executar somente uma tabela:

~~~bash
uv run task gold-load -- --name process_results
~~~

Confira o resultado:

~~~sql
SELECT *
FROM gold.process_results
LIMIT 100;
~~~

Cada execucao faz rebuild atomico: se a query ou transformacao falhar, a tabela
Gold existente continua intacta. Ao trocar o schema ou as colunas da tabela,
execute a recipe novamente e valide os consumidores da tabela.

