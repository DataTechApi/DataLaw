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
              gold.topic_party_results, gold.topic_adherence,
              gold.topic_adherence_evidence
            → Spring Boot dashboard

BNP API → silver.jurisprudencia → gold.topic_precedents
Curated direction → silver.precedente_direcao → gold.topic_adherence,
                                               gold.topic_adherence_evidence
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
| Closed case: latest dated movement is 22 or 246; timestamp ties use the highest movement ID | All Gold recipes |
| Confidential cases (`nivel_sigilo > 0`) are excluded | All Gold recipes, `ProcessoRepository.java` |
| Result: 219 = 1.0, 221 = 0.5, 220 = 0.0 | `topic_results.py`, `process_results.py` |
| Party view: 219 favors the plaintiff, 220 the defendant, 221 counts half for each | `topic_party_results.py`, `ProcessoService.java` |
| Adherence: 219 is adherent to a plaintiff thesis, 220 to a defendant thesis, 221 is partial | `topic_adherence.py` |
| Precedents without a curated direction stay out of the Adherence Index | `topic_adherence.py` |
| Theses with opposite directions are never summed; the dashboard shows the main thesis (largest reliable sample) | `ProcessoService.java` |
| Reliability: no decisions = insufficient, fewer than 30 = low, 30 or more = adequate | `Confiabilidade.java` |
| Evidence uses the same classification as the index, and its totals are checked against the index | `topic_adherence_evidence.py`, `ProcessoService.java` |
| Missing data is null and shown as "Dados insuficientes", never 0% | `ProcessoService.java`, `ProcessoRepository.java`, template |
| Subject volume bars require 30 distinct public cases per subject name; body and class volume bars have no minimum | `ProcessoRepository.java` |
| Success rate by subject: include only court/subject groups with at least 30 closed cases | `topic_results.py` |
| Related precedent list: show precedents only for court/subject groups with at least 30 closed cases | `topic_precedents.py` |
| Precedent link by exact TPU code | `topic_precedents.py`, `topic_adherence.py` |

`topic_results` and `process_results` measure claim outcome. The Adherence Index is in `topic_adherence`.
The [indicator guide](../architecture/indicators.md) defines each metric's
purpose, formula, population, filters, examples and limitations. The
[traceability matrix](../requirements/traceability.md#indicator-rules-and-verification)
connects those rules to requirements, implementation and verification evidence.

## HTTP endpoints

The application has no authentication layer in the repository.

| Method | Path | Parameters | Response |
|---|---|---|---|
| GET | `/`, `/processos/orgaos-julgadores` | Optional `classeNome`, `assuntoNome`, `teseId` | HTML dashboard |
| GET | `/processos/taxa-sucesso` | Required `classeNome` | `{"taxa": number}` |
| GET | `/processos/taxa-sucesso-tema` | Required `assuntoNome` | `{"taxa": number, "precedentes": [...]}` |
| GET | `/processos/indicadores-tema` | Required `assuntoNome`; optional `teseId` | `{"adesao": {...}, "polo": {...}, "adesaoPorOrgao": [...], "adesaoPorTese": [...], "evidencias": {...}}` |

A missing required parameter returns status 400. When there is no data, `taxa` and the indicator percentages are `null`.

On the dashboard, the topic indicators appear when `assuntoNome` is filled.
The adherence and party indicators use partial subject-name matching (`ILIKE`),
like the volume charts. The success-rate endpoints instead use exact class or
subject names. `teseId` selects the thesis shown in the evidence section;
an unknown id falls back to the main thesis. It does not change the main
index, coverage or body comparison.

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

**Record a thesis direction**

The Adherence Index only uses precedents with a curated direction. Until a curation screen exists, a legal reviewer records it with SQL:

```sql
INSERT INTO silver.precedente_direcao (id, jurisprudencia_id, direcao, curador)
VALUES (gen_random_uuid(), '<silver.jurisprudencia.id>', 'autor', '<reviewer name>')
ON CONFLICT (jurisprudencia_id)
DO UPDATE SET direcao = EXCLUDED.direcao, curador = EXCLUDED.curador, curado_em = now();
```

Use `autor`, `reu` or `indefinida`, then run `uv run task gold-load -- --name topic_adherence`.

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
