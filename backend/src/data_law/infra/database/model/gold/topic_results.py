"""Gold recipe for the weighted success rate grouped by TPU subject (tema)."""

from data_law.transformation.gold import register_sql

register_sql(
    "topic_results",
    """
    WITH ultimo_movimento AS (
        SELECT DISTINCT ON (processo_id)
            processo_id,
            codigo,
            data_hora AS data_encerramento
        FROM silver.movimento
        WHERE data_hora IS NOT NULL
        ORDER BY processo_id, data_hora DESC, id DESC
    ),
    processos_encerrados AS (
        SELECT
            p.id AS processo_id,
            p.tribunal_sigla,
            a.codigo AS assunto_codigo,
            a.nome AS assunto_nome,
            u.data_encerramento
        FROM silver.processo AS p
        JOIN silver.processo_assunto AS a
            ON a.processo_id = p.id
        JOIN ultimo_movimento AS u
            ON u.processo_id = p.id
        WHERE u.codigo IN (22, 246)
    ),
    ultimo_julgamento AS (
        SELECT DISTINCT ON (p.processo_id)
            p.processo_id,
            m.codigo AS codigo_resultado
        FROM processos_encerrados AS p
        JOIN silver.movimento AS m
            ON m.processo_id = p.processo_id
        WHERE m.codigo IN (219, 220, 221)
          AND m.data_hora <= p.data_encerramento
        ORDER BY p.processo_id, m.data_hora DESC, m.id DESC
    ),
    resultados AS (
        SELECT
            p.tribunal_sigla,
            p.assunto_codigo,
            p.assunto_nome,
            j.codigo_resultado,
            CASE j.codigo_resultado
                WHEN 219 THEN 1.0
                WHEN 221 THEN 0.5
                WHEN 220 THEN 0.0
            END AS peso_sucesso
        FROM processos_encerrados AS p
        LEFT JOIN ultimo_julgamento AS j
            ON j.processo_id = p.processo_id
    )
    SELECT
        tribunal_sigla,
        assunto_codigo,
        assunto_nome,
        COUNT(*) AS processos_encerrados,
        COUNT(*) FILTER (WHERE peso_sucesso IS NOT NULL) AS processos_com_resultado,
        COUNT(*) FILTER (WHERE peso_sucesso = 1.0) AS favoraveis,
        COUNT(*) FILTER (WHERE peso_sucesso = 0.5) AS parciais,
        COUNT(*) FILTER (WHERE peso_sucesso = 0.0) AS desfavoraveis,
        COUNT(*) FILTER (WHERE peso_sucesso IS NULL) AS sem_resultado_de_merito,
        ROUND(
            100 * AVG(peso_sucesso) FILTER (WHERE peso_sucesso IS NOT NULL),
            2
        ) AS taxa_sucesso_ponderada_pct
    FROM resultados
    GROUP BY tribunal_sigla, assunto_codigo, assunto_nome
    HAVING COUNT(*) >= 30
    ORDER BY taxa_sucesso_ponderada_pct DESC NULLS LAST, processos_com_resultado DESC
    """,
)
