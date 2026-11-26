# Traceability Matrix

This matrix links requirements, business rules, implementation and verification.
Task IDs identify the recorded work items; they do not establish client approval
or production deployment. Implementation status in the Sprint 3 table must be
read separately from the verification and acceptance states below.

## Sprint 3

| Requirement | Requested by | Story | Use case | Task | Code | Tests | Status |
|---|---|---|---|---|---|---|---|
| RF08 | Client | US3.6 | UC-03 | SCRUM-157 | `gold/topic_party_results.py`, `ProcessoService.java`, template | TC-GLD-009, TC-GLD-012, TC-FE-SVC-010, TC-FE-SVC-011, TC-FE-CTL-009, TC-FE-CTL-010 | Implemented |
| RF09 | Client | US3.1 | UC-01 | SCRUM-139 | `gold/topic_adherence.py` (classification) | TC-GLD-010, TC-GLD-013 | Implemented |
| RF10 | Team | US3.1 | UC-01 | SCRUM-139 | `silver/precedent_direction.py`, migration `20261113_08` | TC-INF-005, TC-INF-006, TC-GLD-013 | Partial (curation pending) |
| RF11 | Client | US3.2 | UC-02 | SCRUM-140 | `gold/topic_adherence.py` | TC-GLD-010, TC-GLD-013, TC-GLD-014, TC-FE-SVC-007, TC-FE-SVC-008 | Implemented |
| RNF14 | Client / Team | US3.2 | UC-02 | SCRUM-140 | `Confiabilidade.java` | TC-FE-SVC-009 | Partial |
| RF12 | Client | US3.3 | UC-04 | SCRUM-138 | `ProcessoController`, `ProcessoService`, `orgaos-julgadores.html` | TC-FE-CTL-009 to 014, TC-FE-SVC-012 to 017 | Implemented |
| RF13 | Client | US3.3 | UC-04 | SCRUM-138 | `ProcessoService`, template | TC-FE-SVC-012, TC-FE-CTL-009 | Implemented |
| RF14 | Client | US3.4 | UC-05 | SCRUM-141 | `gold/topic_adherence_evidence.py`, `ProcessoService`, template | TC-GLD-015, TC-GLD-016, TC-FE-CTL-009, TC-FE-CTL-015, TC-FE-SVC-018 to 023 | Implemented |
| RNF13 | Team | US3.2, US3.4 | UC-02, UC-05 | SCRUM-140, SCRUM-141 | Gold recipes, `ProcessoRepository.java` | TC-GLD-011, TC-GLD-012, TC-GLD-013, TC-GLD-016 | Implemented |
| RNF12 | Legal Manager | US3.5 | UC-06 | SCRUM-142 | [Indicator guide](../architecture/indicators.md) | Formula/source review; Product Owner review pending | Documented; acceptance pending |
| RNF10 | Professor | US3.5 | UC-06 | SCRUM-142, SCRUM-95 | This matrix, `docs/requirements/` | Requirement/rule/code/test links below; Product Owner review pending | Partial: delivery and acceptance records pending |

TC IDs are described in [test-cases.md](../testing/test-cases.md). Prefixes without a number cover the whole group. When a planned test is written, add its `TC-` ID here.

## Indicator rules and verification

Each rule links to its definition, formula, population, example and limitations.
RF01/RF06 are broad dashboard requirements; their association with legacy rates
and volumes does not introduce dedicated acceptance criteria that were never
recorded in the requirements.

Implementation paths below are relative to
[`backend/src/data_law/infra/database/model/gold/`](../../backend/src/data_law/infra/database/model/gold/)
for recipes. `repo` refers to
[`ProcessoRepository.java`](../../frontend/src/main/java/com/datatech/datalaw/repository/ProcessoRepository.java),
`service` to
[`ProcessoService.java`](../../frontend/src/main/java/com/datatech/datalaw/service/ProcessoService.java).

| Requirement / rule | Business documentation | Implementation | Verification artifact and scope | Remaining verification or acceptance gap |
|---|---|---|---|---|
| RF09/RF10 — classify against curated direction | [Adherence Index](../architecture/indicators.md#adherence-index) | `topic_adherence.py`; `silver.precedente_direcao` | TC-GLD-010: recipe inspection; TC-GLD-013: PostgreSQL classification in both directions, undefined and missing curation excluded | Legal curation pending; classification is an outcome proxy, not decision-text analysis |
| RF11 — weighted index and missing results | [Adherence Index](../architecture/indicators.md#adherence-index) | `topic_adherence.py`; service `percentual`, `indicadorAdesao` | TC-GLD-013/014: Gold database scenarios; TC-FE-SVC-007/008/012/013: service arithmetic and missing data with mocked repository | Client validation of 0.5 partial weight pending; native aggregation query lacks database execution tests |
| RF13 — coverage | [Coverage](../architecture/indicators.md#coverage) | repo `findAdesaoPorTese`; service `cobertura` | TC-FE-SVC-008/012/013: zero denominator, 50% example, no curated thesis | Service tests do not execute repository SQL; no client acceptance record linked |
| RF08/RF13 — sample size | [Sample size](../architecture/indicators.md#sample-size) | `topic_adherence.py`, `topic_party_results.py`; service DTO construction | TC-GLD-012/013: database counts; TC-FE-SVC-010/012: sample returned by service | Cross-subject aggregation can repeat cases; no distinct cross-subject sample guarantee |
| RNF14/RF13 — reliability category | [Reliability](../architecture/indicators.md#reliability) | `Confiabilidade.paraAmostra`; service | TC-FE-SVC-009: D = 0, 29 and 30 | Legacy subject cutoff uses E rather than D; RNF14 remains partial; client approval not recorded |
| RF08 — plaintiff/defendant split | [Party percentages](../architecture/indicators.md#plaintiff-and-defendant-percentages) | `topic_party_results.py`; repo `findTotaisPorPolo`; service `obterResultadoPorPolo` | TC-GLD-009: inspection; TC-GLD-012: PostgreSQL 6/2/2 scenario; TC-FE-SVC-010/011: mocked service scenarios | Client validation of movement interpretation pending; native aggregation SQL lacks database execution tests |
| RF01/RF06 — legacy class rate (broad scope) | [Weighted rates](../architecture/indicators.md#weighted-success-rates-by-class-and-subject) | `process_results.py`; repo `findTaxaSucessoPorClasse` | TC-GLD-006: registration/SQL inspection; TC-FE-SVC-004: forwards mocked result | No database execution test for recipe arithmetic or native query; combined-court example is illustrative |
| RF01/RF06 — legacy subject rate (broad scope) | [Weighted rates](../architecture/indicators.md#weighted-success-rates-by-class-and-subject) | `topic_results.py`; repo `findTaxaSucessoPorAssunto` | TC-GLD-007: inspection including E >= 30; TC-FE-SVC-005: forwards mocked result | No database execution test for recipe arithmetic, cutoff or native query; example is illustrative |
| RF01/RF06 — volumes (broad scope) | [Case volumes](../architecture/indicators.md#case-volumes-by-judging-body-class-and-subject) | repo `findQuantidadeProcessosPorOrgaoJulgador`, `findQuantidadeProcessosPorClasse`, `findQuantidadeProcessosPorAssunto` | TC-FE-SVC-001/002/003: argument/result forwarding with mocks | Native distinct counting, filters and thresholds lack database execution tests; examples are illustrative |
| RF11/RF12 — body and thesis comparison | [Comparisons](../architecture/indicators.md#adherence-comparisons-by-judging-body-and-thesis) | repo `findAdesaoPorOrgao`, `findAdesaoPorTese`; service `grupo`, `tesePrincipal`, comparison methods | TC-FE-SVC-014/015/016/017: selection, empty results, ranking and metadata; TC-FE-SVC-019: evidence-only thesis selection | Tests mock native query output; no client acceptance record linked |
| RF14 — index evidence | [Evidence boundaries](../architecture/indicators.md#evidence-boundaries-and-acceptance); RF14 in [requirements](requirements.md#rf14--display-the-evidence-behind-the-index) | `topic_adherence_evidence.py`; service `evidencias` | TC-GLD-015/016: inspection/database counts; TC-FE-SVC-018 to 023: mocked evidence behavior | Native evidence queries lack database execution tests; no client acceptance record linked |
| RNF12/RNF10 — documentation and traceability | [Indicator guide](../architecture/indicators.md); this matrix; [UC-06](use-cases.md#uc-06--consult-the-indicator-documentation) | Documentation artifacts | Source/formula cross-check and local link checks; existing test IDs identify evidence, not document acceptance | Product Owner review pending; no dedicated document acceptance test or approval record |

Verification entries describe existing test coverage, not the result of a
particular execution. See [test reports](../testing/test-cases.md) and CI runs
for execution evidence. A passing service test with mocks does not verify its
native database query; a recipe-inspection test does not verify SQL arithmetic
against stored data.

## Change impact and delivery records

When a formula, population or filter changes, follow its row above to update
the business definition, requirement if needed, implementation and affected
tests in the same change. The [Gold materialization contract](../architecture/gold.md)
and [application rules](../code/code-guide.md#key-business-rules) provide the
architecture context; this matrix does not invent a separate architecture
decision record for business rules that have none.

| Record | What must be linked | Current evidence |
|---|---|---|
| Defect | Actual issue ID, affected requirement/rule, reproducing test and fix PR | No defect record is linked for this documentation change; a coverage gap is not itself a recorded defect |
| Delivery | Actual commit/PR and release or deployment record for the relevant requirement | Task IDs are recorded above; no specific delivery or deployment record is linked here |
| Client validation | Reviewer, date, approved rule/version and acceptance artifact | RF08 movement rule, RF10 curation and RF11 partial weight remain pending; no Product Owner approval is linked for RNF12 |

Do not mark a requirement accepted or deployed solely because its implementation
exists or its tests pass. Attach actual delivery and approval records when
available; do not infer them from task IDs or synthetic examples.

## Not covered in Sprint 3

| Item | Decision |
|---|---|
| Doctrine (US2.4) | Out of Sprint 3; no source or doctrine ingestion code exists |
| Average processing time | Secondary for the client; not displayed on the dashboard |
| Performance tuning | Out of Sprint 3, without affecting the index acceptance criteria |
