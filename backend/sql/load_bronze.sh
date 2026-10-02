#!/usr/bin/env bash
# Carrega data/raw/*.json em bronze.datajud_extract e bronze.datajud_hit.
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
    && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"; then
    docker exec -i "$CONTAINER_NAME" \
      psql -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1
  else
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1
  fi
}

# Verifica se existem arquivos
mapfile -t files < <(find data/raw -type f -name '*.json' 2>/dev/null | sort)
if [ "${#files[@]}" -eq 0 ]; then
  echo "Nenhum arquivo JSON encontrado em data/raw" >&2
  exit 1
fi

loaded=0
for file in "${files[@]}"; do
  rel="${file#./}"
  dir="$(basename "$(dirname "$file")")"
  sigla="$(printf '%s' "$dir" | tr '[:lower:]' '[:upper:]')"
  alias_name="api_publica_$(printf '%s' "$dir" | tr '[:upper:]' '[:lower:]')"
  base="$(basename "$file" .json)"

  # Tratamento defensivo de timestamp caso o nome fuja do padrão YYYYMMDD_HHMMSS
  if [[ "$base" =~ ^([0-9]{4})([0-9]{2})([0-9]{2})_?([0-9]{2})([0-9]{2})([0-9]{2}) ]]; then
    when="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]} ${BASH_REMATCH[4]}:${BASH_REMATCH[5]}:${BASH_REMATCH[6]}+00"
  else
    when="$(date -u +"%Y-%m-%d %H:%M:%S+00")"
  fi

  # Usa tag randômica para evitar injeção por colisão de delimitador
  TAG="TAG_$RANDOM"

  {
    cat <<EOF
SET client_encoding = 'UTF8';

WITH ins AS (
  INSERT INTO bronze.datajud_extract (
    tribunal_alias, tribunal_sigla, source_file, extracted_at,
    took_ms, timed_out, shards, hit_count, payload
  )
  SELECT
    '$alias_name',
    '$sigla',
    '$rel',
    TIMESTAMPTZ '$when',
    (j->>'took')::int,
    (j->>'timed_out')::boolean,
    j->'_shards',
    jsonb_array_length(j->'hits'->'hits'),
    j
  FROM (SELECT \$$TAG\$
EOF
    cat "$file"
    cat <<EOF
\$$TAG\$::jsonb AS j) s
  ON CONFLICT (source_file) DO NOTHING
  RETURNING extract_id, payload
)
INSERT INTO bronze.datajud_hit (extract_id, es_index, es_id, es_score, source)
SELECT
  i.extract_id,
  h->>'_index',
  h->>'_id',
  NULLIF(h->>'_score', '')::numeric,
  h->'_source'
FROM ins i
CROSS JOIN LATERAL jsonb_array_elements(i.payload->'hits'->'hits') AS h;
EOF
  } | run_psql

  echo "Carregado: ${rel}"
  loaded=$((loaded + 1))
done

echo "Sucesso: ${loaded} arquivo(s) ingerido(s)."