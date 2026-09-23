# Medallion Architecture

## Purpose

DataLaw ingests DataJud process data from the TJSP and prepares it for future
legal-theme adherence indicators. The current implementation covers the Raw,
Bronze, and Silver layers. Gold metrics and the theme-classification model are
not implemented yet.

The architecture is intentionally incremental and restartable: an unchanged
source payload does not cause a new write in Bronze or a new transformation in
Silver.

## Current Data Flow

```text
DataJud API
    |
    v
Raw files
data/raw/tjsp/ingestion_date=.../run_id=.../page-....json.gz
    |
    v
bronze.datajud_extract
current raw process payload, one row per TJSP/DataJud process
    |
    v
silver.processo ──< silver.movimento
normalized current process and movement data
    |
    v
Gold (planned)
theme-adherence indicators and analytical marts
```

### Raw

Raw stores compressed, immutable API response pages. The directory structure
preserves the tribunal, ingestion date, run identifier, and page number. It is
the audit and recovery source for every later layer.

The current ingestion flow stores only the DataJud process payloads selected by
the configured completion rules. For TJSP, the historical load searches the
last six calendar months for completion movement codes `22` and `246`.
Incremental loads recheck a 48-hour overlap window.

### Bronze

`bronze.datajud_extract` stores one current record for each
`(tribunal_sigla, datajud_id)` pair.

Important columns:

| Column | Purpose |
| --- | --- |
| `payload` | Complete DataJud `_source` object in JSONB |
| `payload_hash` | SHA-256 hash of canonical JSON |
| `source_file` | Raw file that last supplied the process |
| `extracted_at` | Timestamp of the ingestion run |

Bronze uses `INSERT ... ON CONFLICT ... DO UPDATE` only when
`payload_hash` differs. It is therefore a current-state store, not a
historical version store. Raw files retain the immutable source history.

### Silver

Silver normalizes the subset of DataJud data currently required for process and
movement analysis.

#### `silver.processo`

One row per Bronze process extract. It contains process identity, tribunal,
number, jurisdiction level, class, court unit, format, system, confidentiality
level, relevant source timestamps, and the source payload hash.

`bronze_extract_id` is unique, making the Bronze-to-Silver process
relationship one-to-one.

#### `silver.movimento`

One row per distinct current movement of a Silver process. It contains the
movement code, name, timestamp, movement court unit, and
`complementos_tabelados` JSONB.

A movement is identified by a SHA-256 hash of its complete canonical JSON
object. Duplicate movement objects in the same source payload are consolidated.
The unique key is `(processo_id, source_hash)`.

## Silver SCD Type 1 Synchronization

The synchronization service is
`data_law.transformation.silver.sync_bronze_to_silver`.

1. It finds Bronze extracts with no corresponding Silver process or with a
   `payload_hash` different from `silver.processo.source_payload_hash`.
2. It transforms only those pending extracts.
3. It inserts a new Silver process or overwrites the existing row.
4. It inserts or updates current movements and deletes movements no longer
   present in the current Bronze payload.
5. It stores the new source hash only after the process and its movements are
   synchronized in the same database transaction.

This is SCD Type 1: Silver has no version history. A changed payload overwrites
the current normalized representation. The raw layer remains the source for
audit and reprocessing.

Invalid optional dates become `NULL` and produce a warning. Invalid movement
items are ignored with a warning while the original payload remains available in
Bronze.

## Execution

### First local run

```bash
docker compose up -d --wait
uv sync
uv run alembic upgrade head
uv run task full-ingest
```

`full-ingest` saves Raw pages, loads Bronze, and runs a Silver synchronization
after Bronze completes. The ingestion checkpoint is saved only after the Silver
step succeeds.

### Daily incremental run

```bash
uv run python -m data_law.main
```

The command fetches the configured incremental window, upserts Bronze, and
synchronizes only missing or changed Silver processes.

### Reprocess local raw files

```bash
uv run task bronze-load
```

This reads every JSON or JSON.GZ response below `data/raw`, refreshes Bronze,
and then runs the incremental Silver merge.

### Resume or rebuild the pending Silver work

```bash
uv run task silver-load
```

This command reads Bronze directly. It skips Silver rows whose stored source hash
matches the Bronze payload hash, so it safely resumes after interruption.

### Inspect the database

Use any PostgreSQL client. For DBeaver:

```text
Host: localhost
Port: 5432
Database: datalaw_db
User: datalaw
Password: datalaw
JDBC URL: jdbc:postgresql://localhost:5432/datalaw_db
```

Useful queries:

```sql
SELECT *
FROM silver.processo
LIMIT 100;

SELECT classe_nome, count(*) AS total
FROM silver.processo
GROUP BY classe_nome
ORDER BY total DESC
LIMIT 10;
```

## Warehouse Queries

`data_law.warehouse.postgres.PostgresWarehouse` provides read-only
SQLAlchemy queries over Silver:

- `list_processes()` returns recent processes for a tribunal.
- `count_processes_by_class()` returns the most frequent procedural classes.

These helpers are intended for Python consumers. DBeaver or `psql` is better
suited to interactive, ad hoc SQL exploration.

## Decisions

| Decision | Rationale |
| --- | --- |
| PostgreSQL and SQLAlchemy are the operational query layer | The project already uses SQLAlchemy models, Alembic migrations, and PostgreSQL JSONB. |
| Raw is immutable; Bronze and Silver are current state | Raw provides auditability while current-state layers make incremental processing and querying practical. |
| Bronze stores the full source payload as JSONB | The DataJud schema can evolve and Bronze must preserve the source without premature normalization. |
| Silver is limited to processes and movements | This is the smallest useful normalized model for later adherence analysis. Subjects, themes, and evidence are deferred. |
| Silver uses SCD Type 1 and source hashes | The intended analytical view is current state; hashes avoid reprocessing unchanged content. |
| Identical movements are deduplicated | DataJud payloads can contain repeated movement objects; retaining them would inflate later metrics. |
| Silver runs after Bronze as a batch | Bronze is the durable source of truth; a batch dependency keeps the pipeline explicit and restartable. |
| The checkpoint follows Silver success | An ingestion run is not considered complete until its Silver data is current. |
| No additional DataFrame or warehouse engine is used in the ETL | SQLAlchemy and PostgreSQL are sufficient for the current operational flow. DuckDB and Polars remain optional future tools, not pipeline dependencies. |

## Current Limits and Next Steps

- The first Silver backfill can take time because every existing Bronze process
  without a matching Silver hash must be transformed.
- Silver synchronization is restartable and subsequent runs process only changed
  Bronze payloads.
- Gold tables for adherence by theme, period, court unit, and jurisdiction level
  are planned after a theme catalog and a process-to-theme assessment model are
  defined.
- A presentation layer is not part of the current pipeline. DBeaver is suitable
  for database inspection; a future internal dashboard can use a separate
  visualization decision.
