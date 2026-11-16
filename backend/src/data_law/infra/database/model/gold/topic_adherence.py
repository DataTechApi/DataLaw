"""Gold recipe for the Adherence Index by court, judging body, topic and precedent.

Each closed case is compared with every curated precedent of its TPU subject.
With a thesis that favors the plaintiff, 219 is adherent and 220 is not; with a
thesis that favors the defendant, the opposite. 221 is partially adherent.
Precedents without a curated direction (or with ``indefinida``) are left out,
and so are confidential cases (nivel_sigilo > 0).
"""

from data_law.transformation.gold import register_sql

register_sql(
    "topic_adherence",
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
            m.codigo AS codigo_resultado
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
            j.tribunal_sigla AS tribunal_precedente,
            j.identificador_precedente,
            j.titulo AS precedente_titulo,
            d.direcao
        FROM silver.jurisprudencia AS j
        JOIN silver.precedente_direcao AS d
            ON d.jurisprudencia_id = j.id
        WHERE d.direcao IN ('autor', 'reu')
    ),
    classificadas AS (
        SELECT
            p.tribunal_sigla,
            p.orgao_julgador_nome,
            p.assunto_codigo,
            p.assunto_nome,
            t.jurisprudencia_id,
            t.tribunal_precedente,
            t.identificador_precedente,
            t.precedente_titulo,
            t.direcao,
            CASE
                WHEN j.codigo_resultado IS NULL THEN NULL
                WHEN j.codigo_resultado = 221 THEN 'parcial'
                WHEN (j.codigo_resultado = 219 AND t.direcao = 'autor')
                  OR (j.codigo_resultado = 220 AND t.direcao = 'reu')
                    THEN 'aderente'
                ELSE 'nao_aderente'
            END AS classificacao
        FROM processos_encerrados AS p
        JOIN teses AS t
            ON t.assunto_codigo = p.assunto_codigo
        LEFT JOIN ultimo_julgamento AS j
            ON j.processo_id = p.processo_id
    )
    SELECT
        tribunal_sigla,
        orgao_julgador_nome,
        assunto_codigo,
        assunto_nome,
        jurisprudencia_id,
        tribunal_precedente,
        identificador_precedente,
        precedente_titulo,
        direcao,
        COUNT(*) AS processos_encerrados,
        COUNT(classificacao) AS decisoes_com_resultado,
        COUNT(*) FILTER (WHERE classificacao = 'aderente') AS aderentes,
        COUNT(*) FILTER (WHERE classificacao = 'parcial') AS parciais,
        COUNT(*) FILTER (WHERE classificacao = 'nao_aderente') AS nao_aderentes,
        ROUND(
            100.0
            * (
                COUNT(*) FILTER (WHERE classificacao = 'aderente')
                + 0.5 * COUNT(*) FILTER (WHERE classificacao = 'parcial')
            )
            / NULLIF(COUNT(classificacao), 0),
            2
        ) AS indice_adesao_pct,
        now() AS atualizado_em
    FROM classificadas
    GROUP BY
        tribunal_sigla,
        orgao_julgador_nome,
        assunto_codigo,
        assunto_nome,
        jurisprudencia_id,
        tribunal_precedente,
        identificador_precedente,
        precedente_titulo,
        direcao
    ORDER BY decisoes_com_resultado DESC
    """,
)
