# Use Cases — Sprint 3

## UC-01 — Classify decisions against the thesis

| Field | Description |
|---|---|
| Requested by | Client, through the definition of a favorable decision |
| Primary actor | Data pipeline |
| Requirements | RF11, RF12, RF13 |
| Story | US3.1 |
| Preconditions | Silver is up to date and the thesis direction is recorded |
| Postcondition | Each decision with a result has an adherence classification |
| Existing code | `backend/src/data_law/infra/database/model/gold/topic_results.py`, `topic_precedents.py`, `backend/src/data_law/ingestion/jurisprudencia.py` |
| Planned code | Thesis direction column or table, with an Alembic migration, and a Gold classification recipe |
| Existing tests | TC-GLD-007, TC-GLD-008, TC-JUR-012 |

**Happy path**
1. The curator records that the thesis favors the plaintiff.
2. The pipeline loads the closed cases of the topic.
3. The pipeline finds each case's latest merit movement.
4. Movement 219 is classified as adherent.
5. The result becomes available in the Gold layer.

**Alternative paths**
- **Thesis favoring the defendant:** movement 220 is adherent.
- **Movement 221:** the decision is partially adherent.
- **No merit movement:** the case stays out of the denominator.
- **Uncurated thesis:** the precedent stays out of the calculation.

## UC-02 — Calculate the Adherence Index

| Field | Description |
|---|---|
| Requested by | Client: "highest-value metric" |
| Primary actor | Data pipeline |
| Requirements | RF14, RNF14 |
| Story | US3.2 |
| Preconditions | UC-01 is complete |
| Postcondition | Index materialized by court, topic and precedent |
| Existing code | `backend/src/data_law/transformation/gold.py` (materialization) |
| Planned code | `topic_adherence` recipe in `backend/src/data_law/infra/database/model/gold/` |
| Existing tests | TC-GMT-005, TC-GMT-015 |

**Happy path**
1. The operator runs `uv run task gold-load`.
2. The materializer reads the classified decisions.
3. The recipe calculates the index by court, topic and precedent.
4. The Gold table is replaced atomically.

**Alternative paths**
- **Fewer than 30 decisions with a result:** the index is marked low reliability.
- **No decisions with a result:** the index is null.
- **Recipe failure:** the previous table is kept.

## UC-03 — View a topic's Adherence Index

| Field | Description |
|---|---|
| Requested by | Client; serves the Strategic Lawyer and the Legal Manager |
| Primary actor | Strategic Lawyer |
| Requirements | RF02, RF15, RF16, RF18 (conditional) |
| Story | US3.3 |
| Preconditions | Gold is up to date and the user is on the dashboard |
| Postcondition | The user knows the index, sample and reliability |
| Existing code | `ProcessoController.java`, `ProcessoService.java`, `ProcessoRepository.java`, `orgaos-julgadores.html` |
| Planned code | Adherence endpoint and a new `ProcessoRepository` query |
| Existing tests | TC-FE-CTL-007, TC-FE-CTL-008, TC-FE-SVC-005 |

**Happy path**
1. The lawyer opens the dashboard.
2. The lawyer selects a topic.
3. The system highlights the Adherence Index.
4. The system shows sample, coverage, source and update date.
5. The system shows the comparison by judging body.

**Alternative paths**
- **Topic without decisions with a result:** shows "Insufficient data".
- **Topic without a precedent with direction:** states that no curated thesis exists.
- **Small sample:** shows a low-reliability warning.

## UC-04 — View the evidence behind the index

| Field | Description |
|---|---|
| Requested by | Client, through stories 1.4 and 3.5 |
| Primary actor | Legal Manager |
| Requirements | RF17, RNF13 |
| Story | US3.4 |
| Preconditions | Index displayed (UC-03) |
| Postcondition | The user understands how the number was formed |
| Existing code | `findPrecedentesPorAssunto` in `ProcessoRepository.java` |
| Planned code | Query and evidence section in the template |
| Existing tests | TC-FE-SVC-006 |

**Happy path**
1. The manager clicks "View evidence".
2. The system shows the thesis and its direction.
3. The system lists the decisions considered.
4. The manager confirms the totals match the index.

**Alternative paths**
- **Confidential case:** it is neither shown nor counted.
- **No evidence:** shows a message and keeps the index unavailable.

## UC-05 — Consult the indicator documentation

| Field | Description |
|---|---|
| Requested by | Legal Manager (story 3.3) and the DevOps professor |
| Primary actor | Legal Manager |
| Requirements | RNF10, RNF12 |
| Story | US3.5 |
| Preconditions | Formulas validated by the client |
| Postcondition | Each indicator has a formula, assumptions and an example |
| Existing code | `docs/architecture/gold.md`, `docs/requirements/` |
| Planned code | `docs/architecture/indicators.md` |
| Existing tests | Not applicable |

**Happy path**
1. The manager opens the documentation.
2. The manager finds the Adherence Index formula.
3. The manager reproduces the example and reaches the same result.

**Alternative path**
- **Formula changed:** the documentation changes in the same pull request.
