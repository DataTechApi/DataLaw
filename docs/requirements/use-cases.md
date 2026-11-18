# Use Cases — Sprint 3

## UC-01 — Classify decisions against the thesis

| Field | Description |
|---|---|
| Requested by | Client, through the definition of a favorable decision |
| Primary actor | Data pipeline |
| Requirements | RF09, RF10 |
| Story | US3.1 |
| Preconditions | Silver is up to date and the thesis direction is recorded |
| Postcondition | Each decision with a result has an adherence classification |
| Existing code | `backend/src/data_law/infra/database/model/silver/precedent_direction.py`, migration `20261113_08`, `backend/src/data_law/infra/database/model/gold/topic_adherence.py` |
| Planned code | A curation screen or command; today directions are recorded with SQL |
| Existing tests | TC-INF-005, TC-INF-006, TC-GLD-010, TC-GLD-013 |

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
| Requirements | RF11, RNF14 |
| Story | US3.2 |
| Preconditions | UC-01 is complete |
| Postcondition | Index materialized by court, topic and precedent |
| Existing code | `backend/src/data_law/infra/database/model/gold/topic_adherence.py`, `backend/src/data_law/transformation/gold.py` (materialization) |
| Planned code | None |
| Existing tests | TC-GLD-010, TC-GLD-013, TC-GLD-014, TC-GMT-005, TC-GMT-015 |

**Happy path**
1. The operator runs `uv run task gold-load`.
2. The materializer reads the classified decisions.
3. The recipe calculates the index by court, topic and precedent.
4. The Gold table is replaced atomically.

**Alternative paths**
- **Fewer than 30 decisions with a result:** the dashboard marks the index as low reliability.
- **No decisions with a result:** the index is null.
- **Recipe failure:** the previous table is kept.

## UC-03 — View results by party

| Field | Description |
|---|---|
| Requested by | Client (highest-priority view); the movement rule is pending client validation |
| Primary actor | Strategic Lawyer |
| Requirements | RF08 |
| Story | US3.6 |
| Preconditions | Gold is up to date and a topic is selected |
| Postcondition | The user knows how results split between plaintiff and defendant in the topic |
| Existing code | `gold/topic_party_results.py`, `ProcessoRepository.java`, `ProcessoService.java`, `orgaos-julgadores.html` |
| Planned code | None |
| Existing tests | TC-GLD-009, TC-GLD-012, TC-FE-SVC-010, TC-FE-SVC-011, TC-FE-CTL-009, TC-FE-CTL-010 |

**Happy path**
1. The lawyer selects a topic.
2. The system reads the topic's decisions with a result.
3. The system counts 219 for the plaintiff and 220 for the defendant, and treats 221 as partial.
4. The system shows both percentages with the sample size.

**Alternative paths**
- **No decisions with a result:** shows "Insufficient data".
- **Small sample:** shows a low-reliability warning.

## UC-04 — View a topic's Adherence Index

| Field | Description |
|---|---|
| Requested by | Client; serves the Strategic Lawyer and the Legal Manager |
| Primary actor | Strategic Lawyer |
| Requirements | RF12, RF13 |
| Story | US3.3 |
| Preconditions | Gold is up to date and the user is on the dashboard |
| Postcondition | The user knows the index, sample and reliability |
| Existing code | `ProcessoController.java`, `ProcessoService.java`, `ProcessoRepository.java`, `entity/dto/`, `orgaos-julgadores.html` |
| Planned code | None |
| Existing tests | TC-FE-CTL-009 to TC-FE-CTL-014, TC-FE-SVC-007 to TC-FE-SVC-009, TC-FE-SVC-012 to TC-FE-SVC-017 |

**Happy path**
1. The lawyer opens the dashboard.
2. The lawyer selects a topic.
3. The system highlights the Adherence Index of the main thesis, the one with the largest sample.
4. The system shows sample, coverage, reliability, source and update date.
5. The system shows the comparison by judging body for that thesis and the list of theses considered.

**Alternative paths**
- **Topic without decisions with a result:** shows "Insufficient data".
- **Topic without a precedent with direction:** states that no curated thesis exists.
- **Small sample:** shows a low-reliability warning.

## UC-05 — View the evidence behind the index

| Field | Description |
|---|---|
| Requested by | Client, through stories 1.4 and 3.4 |
| Primary actor | Legal Manager |
| Requirements | RF14, RNF13 |
| Story | US3.4 |
| Preconditions | Index displayed (UC-04) |
| Postcondition | The user understands how the number was formed |
| Existing code | `gold/topic_adherence_evidence.py`, `ProcessoRepository.java`, `ProcessoService.java`, `EvidenciasTese.java`, `EvidenciaDecisao.java`, `orgaos-julgadores.html` |
| Planned code | None |
| Existing tests | TC-GLD-015, TC-GLD-016, TC-FE-CTL-009, TC-FE-CTL-015, TC-FE-SVC-018 to TC-FE-SVC-023 |

**Happy path**
1. The manager selects a topic; the evidence section shows the main thesis.
2. The manager clicks "Ver evidências" on another thesis to inspect it.
3. The system shows the thesis and its direction.
4. The system lists the decisions considered: case number, judging body, movement, date and classification.
5. The system shows the totals and confirms they match the index.

**Alternative paths**
- **Confidential case:** it is neither shown nor counted.
- **Topic without a curated thesis:** states that there are no evaluated decisions.
- **More than 50 decisions:** the table shows the 50 most recent; the totals still cover all.
- **Totals differ from the index:** shows a warning to rebuild the Gold layer.

## UC-06 — Consult the indicator documentation

| Field | Description |
|---|---|
| Requested by | Legal Manager (story 3.5) and the DevOps professor |
| Primary actor | Legal Manager |
| Requirements | RNF10, RNF12 |
| Story | US3.5 |
| Preconditions | Documentation is available; client formula validation remains a prerequisite for business acceptance and is still pending |
| Postcondition | Each indicator has a formula, assumptions and an example |
| Existing documentation | [Indicator guide](../architecture/indicators.md), [traceability matrix](traceability.md), `docs/architecture/gold.md` |
| Verification | Existing implementation tests are mapped in the matrix; no dedicated document acceptance test |
| Acceptance | Product Owner review pending; synthetic examples do not establish client approval |

**Happy path**
1. The manager opens the documentation.
2. The manager finds the Adherence Index formula.
3. The manager reproduces the example and reaches the same result.
4. The manager follows the requirement, implementation and verification links,
   distinguishing illustrative calculations from existing test scenarios.

**Alternative path**
- **Formula changed:** the documentation changes in the same pull request.
- **Validation pending:** the manager can inspect the implemented rule and its
  limitations, but the documentation does not present it as client-approved.
