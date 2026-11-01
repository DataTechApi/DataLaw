# Requirements Engineering — DataLaw

This folder holds the **Req Track** block of the DevOps map: from the client's problem to the backlog, code and tests.

| Document | Content |
|---|---|
| [requirements.md](requirements.md) | Functional and non-functional requirements with origin, priority, acceptance criteria and status |
| [use-cases.md](use-cases.md) | Sprint 3 use cases: requester, code, tests, happy path and alternative paths |
| [traceability.md](traceability.md) | Requirement → story → use case → code → test matrix |
| [open-items.md](open-items.md) | Decisions to validate with the client and product gaps |

## Process

The process follows the requirements engineering tasks described by Pressman.

| Task | How it happens in DataLaw |
|---|---|
| Inception | Kick-off with the partner, Xertica, and problem definition |
| Elaboration | Requirements detailed as use cases |
| Negotiation | The Product Owner prioritizes with the client and fits scope to sprint capacity |
| Specification | Recorded in `requirements.md` with verifiable acceptance criteria |
| Validation | Definition of Ready and acceptance tests |
| Management | Stable IDs, Jira (`SCRUM-n`), task IDs in commits and the traceability matrix |

## Traceability flow

```text
Client problem → Requirement (RF/RNF) → Story (US) → Use case (UC)
               → Jira task (SCRUM-n) → Commit/PR → Test (TC) → Deploy
```

## Maintenance rules

1. Never reuse an ID. A requirement removed from scope changes status and stays recorded.
2. Every requirement names who requested it.
3. Every acceptance criterion must be verifiable by a test or a demonstration.
4. A requirement is **Implemented** only when its code and test exist in the repository.
5. When a task is finished, update the traceability matrix in the same pull request.

## Status legend

| Status | Meaning |
|---|---|
| Implemented | Code and automated test exist |
| Partial | Part of the requirement exists; the gap is described |
| Planned | Committed for Sprint 3 |
| Conditional | Depends on a client decision |
| Not implemented | No code, and outside the Sprint 3 commitment |

## Reference

PRESSMAN, Roger S.; MAXIM, Bruce R. *Engenharia de software: uma abordagem profissional*. 9th ed. Porto Alegre: AMGH, 2021.
