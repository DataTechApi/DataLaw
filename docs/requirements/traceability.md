# Traceability Matrix

Sprint 3 Jira tasks still have to be linked. Fill in `SCRUM-n` when they exist.

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
| RNF12 | Legal Manager | US3.5 | UC-06 | SCRUM-142 | `docs/architecture/indicators.md` (planned) | Product Owner review | Planned |
| RNF10 | Professor | US3.5 | UC-06 | SCRUM-142, SCRUM-95 | `docs/requirements/` | Product Owner review | Partial |

TC IDs are described in [test-cases.md](../testing/test-cases.md). Prefixes without a number cover the whole group. When a planned test is written, add its `TC-` ID here.

## Not covered in Sprint 3

| Item | Decision |
|---|---|
| Doctrine (US2.4) | Out of Sprint 3; no source or doctrine ingestion code exists |
| Average processing time | Secondary for the client; not displayed on the dashboard |
| Performance tuning | Out of Sprint 3, without affecting the index acceptance criteria |
