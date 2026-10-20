"""Gold recipe correlating high-volume TPU subjects (N >= 30) with jurisprudence and precedents."""

from data_law.transformation.gold import register_sql

register_sql(
    "topic_precedents",
    """
    WITH topicos_qualificados AS (
        SELECT
            tribunal_sigla,
            assunto_codigo,
            assunto_nome,
            COUNT(*) AS processos_encerrados
        FROM (
            SELECT
                p.id,
                p.tribunal_sigla,
                a.codigo AS assunto_codigo,
                a.nome AS assunto_nome
            FROM silver.processo AS p
            JOIN silver.processo_assunto AS a
                ON a.processo_id = p.id
            JOIN (
                SELECT DISTINCT ON (processo_id)
                    processo_id,
                    codigo
                FROM silver.movimento
                WHERE data_hora IS NOT NULL
                ORDER BY processo_id, data_hora DESC, id DESC
            ) AS u
                ON u.processo_id = p.id
            WHERE u.codigo IN (22, 246)
        ) AS enc
        GROUP BY tribunal_sigla, assunto_codigo, assunto_nome
        HAVING COUNT(*) >= 30
    )
    SELECT
        t.tribunal_sigla,
        t.assunto_codigo,
        t.assunto_nome,
        t.processos_encerrados,
        j.tribunal_sigla AS tribunal_precedente,
        j.identificador_precedente,
        j.titulo AS precedente_titulo,
        j.tese AS precedente_tese,
        j.ementa AS precedente_ementa
    FROM topicos_qualificados AS t
    JOIN silver.jurisprudencia AS j
        ON j.assunto_codigo = t.assunto_codigo
    ORDER BY t.processos_encerrados DESC, j.identificador_precedente ASC
    """,
)
