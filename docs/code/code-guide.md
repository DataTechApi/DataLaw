# Code Guide — DataLaw

## Repository structure

```text
backend/
  src/data_law/
    main.py                 Ingestion entry point
    ingestion/              DataJud client, raw storage, Bronze load, precedents
    transformation/         Silver sync, Gold materializer
    warehouse/              Read queries over PostgreSQL
    infra/database/         SQLAlchemy session and models
      model/gold/           Gold recipes
  migration/                Alembic migrations
  tests/                    pytest suites
frontend/
  src/main/java/.../datalaw/
    controller/             HTTP endpoints
    service/                Application layer
    repository/             Native SQL queries
    entity/                 JPA entity and DTO
  src/main/resources/templates/   Thymeleaf page
  src/test/                 JUnit suites
docs/                       Project documentation
```

## Data flow

```text
DataJud API → raw .json.gz files → bronze.datajud_extract
            → silver.processo, silver.movimento, silver.processo_assunto
            → gold.process_results, gold.topic_results, gold.topic_precedents
            → Spring Boot dashboard

BNP API → silver.jurisprudencia → gold.topic_precedents
```

## Layer rules

| Layer | Rule |
|---|---|
| Raw | Immutable API pages, used for audit and reprocessing |
| Bronze | One current row per `(tribunal_sigla, datajud_id)`, updated only when `payload_hash` changes ([ADR](../../ADR.md)) |
| Silver | Clean, typed data, synchronized only for new or changed extracts |
| Gold | Tables fully rebuilt from Silver by read-only recipes |

## Backend modules

| Module | Responsibility |
|---|---|
| `ingestion/ingestion.py` | Historical and incremental loads, pagination and checkpoints |
| `ingestion/bronze.py` | Raw file processing, upserts and `TRIBUNAL_METADATA` |
| `ingestion/storage.py` | Partitioned gzip raw files |
| `ingestion/jurisprudencia.py` | BNP search and precedent persistence |
| `transformation/silver.py` | Bronze to Silver synchronization |
| `transformation/gold.py` | Recipe registry, SQL validation and atomic materialization |
| `transformation/gold_recipes.py` | Loads project recipes |
| `warehouse/postgres.py` | Read access to analytical data |

## Key business rules

| Rule | Location |
|---|---|
| Closed case: latest movement is 22 or 246 | `topic_results.py`, `process_results.py` |
| Result: 219 = 1.0, 221 = 0.5, 220 = 0.0 | `topic_results.py`, `process_results.py` |
| Minimum of 30 closed cases per topic | `topic_results.py`, `topic_precedents.py`, `ProcessoRepository.java` |
| Precedent link by exact TPU code | `topic_precedents.py` |

The current rate measures claim outcome, not the Adherence Index. See the [requirements](../requirements/requirements.md).

## HTTP endpoints

The application has no authentication layer in the repository.

| Method | Path | Parameters | Response |
|---|---|---|---|
| GET | `/`, `/processos/orgaos-julgadores` | Optional `classeNome`, `assuntoNome` | HTML dashboard |
| GET | `/processos/taxa-sucesso` | Required `classeNome` | `{"taxa": number}` |
| GET | `/processos/taxa-sucesso-tema` | Required `assuntoNome` | `{"taxa": number, "precedentes": [...]}` |

A missing required parameter returns status 400.

## How to extend

**Add a court**

1. Add it to `TRIBUNAL_METADATA` in `bronze.py`.
2. Run its historical load.
3. Add tests for the new metadata.
4. Check indicators that aggregate across courts.

**Add a Gold table**

1. Create a recipe in `infra/database/model/gold/`.
2. Import it in `gold_recipes.py`.
3. Add a test in `tests/transformation/test_gold.py`.
4. Run `uv run task gold-load -- --name <table>`.

Full rules are in [gold.md](../architecture/gold.md). Recipes read only from `silver`.

**Change the schema**

```bash
cd backend
uv run alembic revision --autogenerate -m "describe the change"
```

Review the generated file, apply it locally and commit it with the model.

**Add a dashboard indicator**

1. Add the query to `ProcessoRepository`, reading from Gold.
2. Expose it through `ProcessoService` and `ProcessoController`.
3. Render it in `orgaos-julgadores.html`.
4. Add controller and service tests.

Keep null separate from zero, so that missing data is never displayed as 0%.

## Conventions

- Python: `ruff` with line length 88, and type hints checked by `mypy`.
- Java: controller → service → repository, with constructor injection.
- SQL: bound parameters only, never string concatenation of user input.
- Language: new documentation is in English. Domain names such as `processo` and `assunto` stay in Portuguese to match the data.

## Related documents

- [Data dictionary](../architecture/data-dictionary.md)
- [Medallion architecture](../architecture/medallion.md)
- [Precedents strategy](../architecture/jurisprudencia-e-precedentes.md)
- [DataJud codes](../datajud/codigos-api.md)
