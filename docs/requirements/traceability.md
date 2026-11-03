# Traceability Matrix

Sprint 3 Jira tasks still have to be linked. Fill in `SCRUM-n` when they exist.

## Sprint 3

| Requirement | Requested by | Story | Use case | Task | Code | Tests | Status |
|---|---|---|---|---|---|---|---|
| RF08 | Client | US3.6 | UC-03 | SCRUM-157 | `gold/topic_results.py`, `ProcessoRepository.java`, template | TC-GLD-007; planned: 60/20/20 scenario and empty topic | Planned |
| RF09 | Client | US3.1 | UC-01 | SCRUM-139 | Gold classification recipe (planned) | Planned: both thesis directions, partial and uncurated thesis | Planned |
| RF10 | Team | US3.1 | UC-01 | SCRUM-139 | Migration and model (planned) | Planned: direction values and uncurated precedent | Planned |
| RF11 | Client | US3.2 | UC-02 | SCRUM-140 | `topic_adherence` (planned) | TC-GMT-005, TC-GMT-015; planned: closed scenario and null index | Planned |
| RNF14 | Client / Team | US3.2 | UC-02 | SCRUM-140 | `topic_adherence` (planned) | Planned: 29 decisions marked low reliability | Partial |
| RF12 | Client | US3.3 | UC-04 | SCRUM-138 | `ProcessoController`, `orgaos-julgadores.html` | TC-FE-CTL-007, TC-FE-CTL-008; planned: null index shows "Insufficient data" | Planned |
| RF13 | Client | US3.3 | UC-04 | SCRUM-138 | `ProcessoRepository`, template | TC-FE-SVC-005; planned: sample, coverage and warning | Planned |
| RF14 | Client | US3.4 | UC-05 | SCRUM-141 | `ProcessoRepository`, template | TC-FE-SVC-006; planned: totals match the index | Planned |
| RNF13 | Team | US3.2, US3.4 | UC-02, UC-05 | SCRUM-140, SCRUM-141 | Recipes and queries | Planned: confidential case excluded | Partial |
| RNF12 | Legal Manager | US3.5 | UC-06 | SCRUM-142 | `docs/architecture/indicators.md` (planned) | Product Owner review | Planned |
| RNF10 | Professor | US3.5 | UC-06 | SCRUM-142, SCRUM-95 | `docs/requirements/` | Product Owner review | Partial |

TC IDs are described in [test-cases.md](../testing/test-cases.md). Prefixes without a number cover the whole group. When a planned test is written, add its `TC-` ID here.

## Not covered in Sprint 3

| Item | Decision |
|---|---|
| Doctrine (US2.4) | Out of Sprint 3; no source or doctrine ingestion code exists |
| Average processing time | Secondary for the client; not displayed on the dashboard |
| Performance tuning | Out of Sprint 3, without affecting the index acceptance criteria |
