# Open Requirements Items

## Decisions to validate with the client

| ID | Question | Proposal | Impact |
|---|---|---|---|
| P1 | Should the screen highlight thesis adherence, results by party, or both side by side? | Show both side by side, since the client prioritizes the party view | Defines RF08 and RF12 |
| P2 | How much is a partial decision worth? | Weight of 0.5, as in the current calculation | Changes the RF11 formula and the RF08 rule |
| P3 | Is manual curation of the thesis direction acceptable? | Curate precedents for pilot topics | Defines the index reach |
| P4 | Does "appeal granted" enter the index? | Not this sprint. The verified sample holds only first-instance and special-court cases, with no 237, 238 or 239 movements | May require new ingestion |
| P5 | What client reference number validates the index? | Request at least one topic with a known value | Required by the Definition of Done |
| P6 | Can plaintiff and defendant results be measured by merit movements (219 favors the plaintiff, 220 the defendant, 221 counts as half for each)? | Use the movement rule, since the public data has no parties or decision text | Defines RF08 and US3.6 |

## Product gaps

| ID | Gap | Evidence | Treatment |
|---|---|---|---|
| L1 | The current rate measures claim outcome, not thesis adherence | `topic_results.py` scores 219 as 1, 221 as 0.5 and 220 as 0, ignoring the precedent | US3.1 and US3.2 |
| L2 | Missing data appears as 0% | `COALESCE(..., 0)` in `ProcessoRepository.java` and `data.taxa \|\| 0` in the template | RF11 and RF12 |
| L3 | The N ≥ 30 cut uses closed cases, not decisions with a result | `HAVING COUNT(*) >= 30` in `topic_results.py` | RNF14 |
| L4 | Confidential cases are not filtered | `nivel_sigilo` is mapped, but no filter exists in Gold recipes or frontend Java; the precedents document promises exclusion | RNF13 |
| L5 | Result coverage may be low | 16 movements 219, 220 or 221 in one page of 500 cases (a sample, not a full measure) | Measure real coverage before promising values |
| L6 | Payload has no decision text or parties | `_source` fields in a `data/raw` sample | Motivates RF10 and the movement-based party rule (RF08) |
| L7 | Only TJSP is configured | `TRIBUNAL_METADATA` in `bronze.py` | Review Sprint 2 story US2.5 in Jira |
| L8 | Doctrine has no implemented source | Code search found no doctrine ingestion | Out of Sprint 3; inform the client |
