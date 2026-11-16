"""Gold recipe splitting merit results between plaintiff and defendant by topic.

Movement 219 (procedência) favors the plaintiff, 220 (improcedência) favors the
defendant and 221 (procedência em parte) counts as half for each side.
Confidential cases (nivel_sigilo > 0) are excluded.
"""

from data_law.transformation.gold import register_sql

register_sql(
    "topic_party_results",
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
          AND COALESCE(p.nivel_sigilo, 0) = 0
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
    )
    SELECT
        p.tribunal_sigla,
        p.assunto_codigo,
        p.assunto_nome,
        COUNT(*) AS processos_encerrados,
        COUNT(j.codigo_resultado) AS decisoes_com_resultado,
        COUNT(*) FILTER (WHERE j.codigo_resultado = 219) AS procedentes,
        COUNT(*) FILTER (WHERE j.codigo_resultado = 221) AS parciais,
        COUNT(*) FILTER (WHERE j.codigo_resultado = 220) AS improcedentes,
        ROUND(
            100.0
            * (
                COUNT(*) FILTER (WHERE j.codigo_resultado = 219)
                + 0.5 * COUNT(*) FILTER (WHERE j.codigo_resultado = 221)
            )
            / NULLIF(COUNT(j.codigo_resultado), 0),
            2
        ) AS autor_pct,
        ROUND(
            100.0
            * (
                COUNT(*) FILTER (WHERE j.codigo_resultado = 220)
                + 0.5 * COUNT(*) FILTER (WHERE j.codigo_resultado = 221)
            )
            / NULLIF(COUNT(j.codigo_resultado), 0),
            2
        ) AS reu_pct,
        now() AS atualizado_em
    FROM processos_encerrados AS p
    LEFT JOIN ultimo_julgamento AS j
        ON j.processo_id = p.processo_id
    GROUP BY p.tribunal_sigla, p.assunto_codigo, p.assunto_nome
    ORDER BY decisoes_com_resultado DESC
    """,
)
