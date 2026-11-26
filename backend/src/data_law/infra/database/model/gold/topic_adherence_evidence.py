"""Gold recipe listing the decisions behind the Adherence Index (evidence).

One row per decision with a merit result and per curated precedent of its TPU
subject, classified with the same rule as ``topic_adherence``, so the rows of a
precedent add up to its ``decisoes_com_resultado``. Confidential cases
(nivel_sigilo > 0) are excluded and no party data is selected.
"""

from data_law.transformation.gold import register_sql

register_sql(
    "topic_adherence_evidence",
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
            p.numero_processo,
            p.orgao_julgador_nome,
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
            m.codigo AS codigo_resultado,
            m.nome AS movimento_nome,
            m.data_hora AS data_julgamento
        FROM processos_encerrados AS p
        JOIN silver.movimento AS m
            ON m.processo_id = p.processo_id
        WHERE m.codigo IN (219, 220, 221)
          AND m.data_hora <= p.data_encerramento
        ORDER BY p.processo_id, m.data_hora DESC, m.id DESC
    ),
    teses AS (
        SELECT
            j.id AS jurisprudencia_id,
            j.assunto_codigo,
            d.direcao
        FROM silver.jurisprudencia AS j
        JOIN silver.precedente_direcao AS d
            ON d.jurisprudencia_id = j.id
        WHERE d.direcao IN ('autor', 'reu')
    )
    SELECT
        p.tribunal_sigla,
        p.orgao_julgador_nome,
        p.assunto_codigo,
        p.assunto_nome,
        t.jurisprudencia_id,
        t.direcao,
        p.numero_processo,
        j.codigo_resultado,
        j.movimento_nome,
        j.data_julgamento,
        CASE
            WHEN j.codigo_resultado = 221 THEN 'parcial'
            WHEN (j.codigo_resultado = 219 AND t.direcao = 'autor')
              OR (j.codigo_resultado = 220 AND t.direcao = 'reu')
                THEN 'aderente'
            ELSE 'nao_aderente'
        END AS classificacao,
        now() AS atualizado_em
    FROM processos_encerrados AS p
    JOIN teses AS t
        ON t.assunto_codigo = p.assunto_codigo
    JOIN ultimo_julgamento AS j
        ON j.processo_id = p.processo_id
    ORDER BY j.data_julgamento DESC
    """,
)
