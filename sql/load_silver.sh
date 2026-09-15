#!/usr/bin/env bash
# Popula silver a partir de bronze.datajud_hit.
# Linux:  ./sql/load_silver.sh
# Windows (Git Bash / WSL):  bash sql/load_silver.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONTAINER_NAME="${DATALAW_DB_CONTAINER:-datalaw_db}"
PGUSER="${POSTGRES_USER:-datalaw}"
PGDATABASE="${POSTGRES_DB:-datalaw_db}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"
export PGPASSWORD="${POSTGRES_PASSWORD:-datalaw}"

run_psql() {
  if command -v docker >/dev/null 2>&1 \
    && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
  then
    docker exec -i "$CONTAINER_NAME" \
      psql -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 --single-transaction
  else
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
      -v ON_ERROR_STOP=1 --single-transaction
  fi
}

run_psql <<'SQL'
SET client_encoding = 'UTF8';

INSERT INTO silver.tribunal (sigla, nome)
SELECT DISTINCT
    source->>'tribunal' AS sigla,
    source->>'tribunal' AS nome
FROM bronze.datajud_hit
WHERE source->>'tribunal' IS NOT NULL
ON CONFLICT (sigla) DO NOTHING;

INSERT INTO silver.grau (codigo, descricao)
SELECT DISTINCT
    source->>'grau' AS codigo,
    source->>'grau' AS descricao
FROM bronze.datajud_hit
WHERE source->>'grau' IS NOT NULL
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO silver.classe_processual (codigo, nome)
SELECT DISTINCT
    ((source->'classe'->>'codigo')::integer) AS codigo,
    source->'classe'->>'nome' AS nome
FROM bronze.datajud_hit
WHERE source->'classe'->>'codigo' IS NOT NULL
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome;

INSERT INTO silver.sistema (codigo, nome)
SELECT DISTINCT
    ((source->'sistema'->>'codigo')::integer) AS codigo,
    source->'sistema'->>'nome' AS nome
FROM bronze.datajud_hit
WHERE source->'sistema'->>'codigo' IS NOT NULL
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO silver.formato (codigo, nome)
SELECT DISTINCT
    ((source->'formato'->>'codigo')::integer) AS codigo,
    source->'formato'->>'nome' AS nome
FROM bronze.datajud_hit
WHERE source->'formato'->>'codigo' IS NOT NULL
ON CONFLICT (codigo) DO NOTHING;

WITH orgaos_combinados AS (
    SELECT
        (source->'orgaoJulgador'->>'codigo')::integer AS codigo,
        source->'orgaoJulgador'->>'nome' AS nome,
        (source->'orgaoJulgador'->>'codigoMunicipioIBGE')::integer AS codigo_municipio_ibge,
        source->>'tribunal' AS tribunal_sigla
    FROM bronze.datajud_hit
    WHERE source->'orgaoJulgador'->>'codigo' IS NOT NULL
      AND source->>'tribunal' IS NOT NULL

    UNION

    SELECT
        (m->'orgaoJulgador'->>'codigo')::integer AS codigo,
        COALESCE(m->'orgaoJulgador'->>'nome', 'Não informado') AS nome,
        (m->'orgaoJulgador'->>'codigoMunicipioIBGE')::integer AS codigo_municipio_ibge,
        h.source->>'tribunal' AS tribunal_sigla
    FROM bronze.datajud_hit h
    CROSS JOIN LATERAL jsonb_array_elements(h.source->'movimentos') AS m
    WHERE m->'orgaoJulgador'->>'codigo' IS NOT NULL
      AND h.source->>'tribunal' IS NOT NULL
)
INSERT INTO silver.orgao_julgador (codigo, nome, codigo_municipio_ibge, tribunal_sigla)
SELECT DISTINCT ON (codigo)
    codigo,
    nome,
    codigo_municipio_ibge,
    tribunal_sigla
FROM orgaos_combinados
ORDER BY codigo
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome,
    codigo_municipio_ibge = COALESCE(
        EXCLUDED.codigo_municipio_ibge,
        silver.orgao_julgador.codigo_municipio_ibge
    );

INSERT INTO silver.assunto (codigo, nome)
SELECT DISTINCT
    ((a->>'codigo')::integer) AS codigo,
    a->>'nome' AS nome
FROM bronze.datajud_hit h
CROSS JOIN LATERAL jsonb_array_elements(h.source->'assuntos') AS a
WHERE a->>'codigo' IS NOT NULL
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome;

INSERT INTO silver.tipo_movimento (codigo, nome)
SELECT DISTINCT
    ((m->>'codigo')::integer) AS codigo,
    m->>'nome' AS nome
FROM bronze.datajud_hit h
CROSS JOIN LATERAL jsonb_array_elements(h.source->'movimentos') AS m
WHERE m->>'codigo' IS NOT NULL
ON CONFLICT (codigo) DO UPDATE
SET nome = COALESCE(EXCLUDED.nome, silver.tipo_movimento.nome);

WITH comps AS (
    SELECT DISTINCT
        ((c->>'codigo')::integer) AS tipo_codigo,
        c->>'descricao' AS tipo_descricao,
        ((c->>'valor')::integer) AS valor,
        c->>'nome' AS nome
    FROM bronze.datajud_hit h
    CROSS JOIN LATERAL jsonb_array_elements(h.source->'movimentos') AS m
    CROSS JOIN LATERAL jsonb_array_elements(m->'complementosTabelados') AS c
    WHERE c->>'codigo' IS NOT NULL AND c->>'valor' IS NOT NULL
),
ins_tipo AS (
    INSERT INTO silver.tipo_complemento (codigo, descricao)
    SELECT DISTINCT tipo_codigo, COALESCE(tipo_descricao, 'Sem descrição')
    FROM comps
    ON CONFLICT (codigo) DO NOTHING
)
INSERT INTO silver.valor_complemento (tipo_complemento_codigo, valor, nome)
SELECT DISTINCT tipo_codigo, valor, COALESCE(nome, 'Sem descrição')
    FROM comps
ON CONFLICT (tipo_complemento_codigo, valor) DO UPDATE
SET nome = EXCLUDED.nome;

INSERT INTO silver.processo (
    id_datajud,
    numero_processo,
    tribunal_sigla,
    grau,
    classe_codigo,
    sistema_codigo,
    formato_codigo,
    orgao_julgador_codigo,
    nivel_sigilo,
    data_ajuizamento,
    data_hora_ultima_atualizacao,
    source_extract_id
)
SELECT
    source->>'id' AS id_datajud,
    source->>'numeroProcesso' AS numero_processo,
    source->>'tribunal' AS tribunal_sigla,
    source->>'grau' AS grau,
    (source->'classe'->>'codigo')::integer AS classe_codigo,
    (source->'sistema'->>'codigo')::integer AS sistema_codigo,
    (source->'formato'->>'codigo')::integer AS formato_codigo,
    (source->'orgaoJulgador'->>'codigo')::integer AS orgao_julgador_codigo,
    COALESCE((source->>'nivelSigilo')::integer, 0) AS nivel_sigilo,
    CASE
        WHEN (source->>'dataAjuizamento') ~ '^\d{14}$'
            THEN to_timestamp(source->>'dataAjuizamento', 'YYYYMMDDHH24MISS')
        ELSE (source->>'dataAjuizamento')::timestamptz
    END AS data_ajuizamento,
    (source->>'dataHoraUltimaAtualizacao')::timestamptz AS data_hora_ultima_atualizacao,
    extract_id AS source_extract_id
FROM bronze.datajud_hit
ON CONFLICT (id_datajud) DO UPDATE
SET data_hora_ultima_atualizacao = EXCLUDED.data_hora_ultima_atualizacao,
    nivel_sigilo = EXCLUDED.nivel_sigilo;

INSERT INTO silver.processo_assunto (processo_sk, assunto_codigo)
SELECT DISTINCT
    p.processo_sk,
    (a->>'codigo')::integer AS assunto_codigo
FROM bronze.datajud_hit h
JOIN silver.processo p ON p.id_datajud = h.source->>'id'
CROSS JOIN LATERAL jsonb_array_elements(h.source->'assuntos') AS a
WHERE a->>'codigo' IS NOT NULL
ON CONFLICT (processo_sk, assunto_codigo) DO NOTHING;

INSERT INTO silver.movimento (
    processo_sk,
    tipo_movimento_codigo,
    data_hora,
    orgao_julgador_codigo,
    nome_origem,
    ordem_origem
)
SELECT
    p.processo_sk,
    (m.value->>'codigo')::integer AS tipo_movimento_codigo,
    (m.value->>'dataHora')::timestamptz AS data_hora,
    COALESCE(
        (m.value->'orgaoJulgador'->>'codigo')::integer,
        p.orgao_julgador_codigo
    ) AS orgao_julgador_codigo,
    m.value->>'nome' AS nome_origem,
    (m.ordem - 1)::integer AS ordem_origem
FROM bronze.datajud_hit h
JOIN silver.processo p ON p.id_datajud = h.source->>'id'
CROSS JOIN LATERAL jsonb_array_elements(h.source->'movimentos')
    WITH ORDINALITY AS m(value, ordem)
WHERE (m.value->>'codigo') IS NOT NULL
ON CONFLICT (processo_sk, ordem_origem) DO UPDATE
SET nome_origem = EXCLUDED.nome_origem,
    data_hora = EXCLUDED.data_hora;

INSERT INTO silver.movimento_complemento (
    movimento_sk,
    tipo_complemento_codigo,
    valor,
    nome_origem
)
SELECT
    mov.movimento_sk,
    (c->>'codigo')::integer AS tipo_complemento_codigo,
    (c->>'valor')::integer AS valor,
    COALESCE(c->>'nome', c->>'descricao', 'Não informado') AS nome_origem
FROM bronze.datajud_hit h
JOIN silver.processo p ON p.id_datajud = h.source->>'id'
CROSS JOIN LATERAL jsonb_array_elements(h.source->'movimentos')
    WITH ORDINALITY AS m(value, ordem)
JOIN silver.movimento mov
    ON mov.processo_sk = p.processo_sk
   AND mov.ordem_origem = (m.ordem - 1)::integer
CROSS JOIN LATERAL jsonb_array_elements(m.value->'complementosTabelados') AS c
WHERE c->>'codigo' IS NOT NULL AND c->>'valor' IS NOT NULL
ON CONFLICT (movimento_sk, tipo_complemento_codigo, valor) DO NOTHING;
SQL

echo "Silver populada a partir da bronze."