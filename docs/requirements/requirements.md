# Requirements Specification — DataLaw

Sprint 3 revision. Functional requirements were renumbered in this revision: RF01–RF07 are the revised original requirements and RF08–RF14 are the Sprint 3 requirements. Non-functional IDs RNF01–RNF11 were kept.

## 1. Client definitions

These statements drive Sprint 3 priorities. They are translated from Portuguese; the original wording is kept below each one.

> Highest-value metric: Adherence Index (%) to the topic/precedent. It is the heart of Legal Analytics. Average time and archival rate are secondary and offer little strategic intelligence because their averages are widely known.

*Original: "Métrica de maior valor: Índice de Adesão (%) ao tema/precedente. É o coração do Legal Analytics. Tempo médio e taxa de arquivamento são secundários e trazem pouca inteligência estratégica pois são valores amplamente conhecidos na média."*

> Definition of a favorable decision: favorable to the researched thesis/topic (and/or the appeal being granted). The focus is whether the judgment accepted the legal position under analysis, regardless of plaintiff or defendant.

*Original: "Definição de decisão favorável: Favorável à tese/tema pesquisado (e/ou provimento do recurso). O foco é saber se o julgado acolheu a posição jurídica analisada, independentemente de ser autor ou réu."*

> Generic success rates and probabilistic predictions have limited value, because statistics do not support a legal brief. Thesis adherence delivers the strategy: knowing which thesis won and in favor of whom gives the lawyer the exact argument. The greatest value is to connect theses and qualified precedents (art. 927 of the Code of Civil Procedure).

*Summary of the client's answer of 2026-11-13. The original message is in Portuguese.*

## 2. Glossary

| Term | Definition |
|---|---|
| Topic | Subject in the Unified Procedural Table (TPU) |
| Precedent | Qualified thesis from STJ, STF or TJs |
| Thesis direction | Party the thesis benefits: `plaintiff`, `defendant` or `undefined` |
| Decision with a result | Closed case whose selected result is the latest movement 219, 220 or 221 dated on or before closure |
| Adherent decision | Decision whose selected claim outcome matches the curated thesis direction; an outcome-based proxy, not a check of the decision text |
| Adherence Index | Weighted percentage: `100 × (adherent + 0.5 × partial) / decisions with a result`; see the [indicator guide](../architecture/indicators.md#adherence-index) |

## 3. Functional requirements

### 3.1 Highest-value requirements (Sprint 3)

#### RF08 — Display the view by party

- **Requested by:** client (highest-priority view)
- **Priority:** Highest
- **Status:** Implemented
- **Description:** the system must show how results split between plaintiff and defendant in the selected topic.
- **Proposed rule:** movement 219 favors the plaintiff, 220 favors the defendant and 221 counts as half for each. The calculation does not need to identify the parties.
- **Acceptance criteria:**
  - A topic with 60 movements 219, 20 of 221 and 20 of 220 shows 70% for the plaintiff and 30% for the defendant.
  - The sample size is shown next to the percentages.
  - A topic without decisions with a result shows "Insufficient data", never 0%.
- **Implementation:** `gold.topic_party_results` and the "Resultados por Polo" card.
- **Pending:** client validation of the movement rule. The client's answer of 2026-11-13 indicates that the split gains value when shown by thesis.

#### RF09 — Classify the decision against the thesis

- **Requested by:** client
- **Priority:** High
- **Status:** Implemented
- **Description:** the system must classify each decision with a result as adherent, partially adherent or non-adherent to the analyzed thesis.
- **Acceptance criteria:**
  - Thesis favoring the plaintiff: movement 219 is adherent and 220 is non-adherent.
  - Thesis favoring the defendant: movement 220 is adherent and 219 is non-adherent.
  - Movement 221 is partially adherent in both directions.
  - A thesis with `undefined` direction is left out of the calculation.
  - A case without a merit movement stays out of the denominator.

#### RF10 — Record the thesis direction

- **Requested by:** team, to enable the client's definition
- **Priority:** High
- **Status:** Partial
- **Description:** each precedent used in the index must have its thesis direction recorded, with curator and date.
- **Reason:** the sampled DataJud payload has no decision text, and the BNP data in use does not state which party a thesis benefits.
- **Acceptance criteria:**
  - Direction accepts only `plaintiff`, `defendant` or `undefined`.
  - The record stores curator and date.
  - A precedent without curation is treated as `undefined`.
- **Implementation:** table `silver.precedente_direcao`, with the values `autor`, `reu` and `indefinida`.
- **Pending:** the legal curation itself. There is no curation screen; directions are recorded with SQL, as described in the [code guide](../code/code-guide.md).

#### RF11 — Calculate the Adherence Index

- **Requested by:** client
- **Priority:** High
- **Status:** Implemented
- **Description:** the system must calculate the Adherence Index by court, judging body, topic and precedent in the Gold layer (`gold.topic_adherence`).
- **Proposed formula:**

```text
Adherence Index (%) = 100 × (adherent + 0.5 × partial) / decisions with a result
```

- **Acceptance criteria:**
  - The formula is tested with closed scenarios in both thesis directions.
  - With no decisions with a result, the index is null, not 0%.
  - Theses with opposite directions are never summed, because their indexes would cancel out.
- **Pending:** client validation of the 0.5 weight for partial decisions.

#### RF12 — Display the Adherence Index as the main indicator

- **Requested by:** client
- **Priority:** High
- **Status:** Implemented
- **Description:** when a topic is selected, the user must first see the Adherence Index of the main thesis and the comparison by judging body for that thesis. The main thesis is the one with the most reliable and largest sample. Average time and archival stay secondary.
- **Acceptance criteria:**
  - The index has greater visual emphasis than secondary indicators.
  - The comparison sorts judging bodies by index.
  - A topic without data shows "Insufficient data", never 0%.

#### RF13 — Show indicator source and reliability

- **Requested by:** client (story 1.4)
- **Priority:** Medium
- **Status:** Implemented
- **Description:** the index must show source, update date, sample size and coverage.
- **Acceptance criteria:**
  - Shows the totals of decisions with a result and closed cases.
  - Shows coverage: decisions with a result ÷ closed cases.
  - A sample below the RNF14 minimum shows a low-reliability warning.

#### RF14 — Display the evidence behind the index

- **Requested by:** client (story 3.4)
- **Priority:** Medium
- **Status:** Implemented
- **Description:** from the index, the user must be able to open the cases and the precedent that support the calculation.
- **Acceptance criteria:**
  - Lists case number, judging body, movement, date and classification.
  - Shows the thesis and direction used in the calculation.
  - The list totals match the value shown in the indicator.
  - No case with `nivel_sigilo > 0` appears.
- **Implementation:** `gold.topic_adherence_evidence` and the "Evidências do Índice" section. The section shows the main thesis by default; "Ver evidências" on each thesis selects it. The table lists the 50 most recent decisions, the totals cover all of them, and a check states whether they match the index.

### 3.2 Revised original requirements

| ID | Requirement | Priority | Status | Current code |
|---|---|---|---|---|
| RF01 | Single-screen metrics | High | Partial | Adherence, party view and volumes on one screen; processing time is not displayed |
| RF02 | DataJud extraction | Critical | Implemented | Only TJSP is configured |
| RF03 | Open data extraction | High | Partial | BNP integration exists |
| RF04 | Cleaning and standardization | Critical | Implemented | Bronze and Silver layers |
| RF05 | Dimensional storage | High | Partial | Aggregated Gold tables exist; no fact and dimension tables |
| RF06 | Indicator dashboards | High | Partial | Volume dashboard exists; processing time is not displayed |
| RF07 | Outcome classification | Critical | Partial | Claim outcome is classified; adherence is detailed in RF09 |

## 4. Non-functional requirements

| ID | Requirement | Priority | Status | Verification |
|---|---|---|---|---|
| RNF01 | Data model documentation | Medium | Partial | Dictionary in `docs/architecture/data-dictionary.md` |
| RNF02 | API documentation | Medium | Implemented | [Code guide](../code/code-guide.md) lists every endpoint |
| RNF03 | Backend in Python | Critical | Implemented | `backend/` |
| RNF04 | Frontend in Java | Critical | Implemented | `frontend/` |
| RNF05 | Unit and integration tests | High | Partial | Unit suites exist; Gold indicator recipes have integration tests; native queries of `ProcessoRepository` are pending |
| RNF06 | Functional tests | Medium | Partial | Controller tests exist; no UI tests |
| RNF07 | Continuous static analysis | Medium | Partial | `ruff` runs in CI; `mypy` is manual; no SonarQube configuration in the repository |
| RNF08 | CI/CD | High | Implemented | `.github/workflows/deploy.yml` |
| RNF09 | Civil law scope | High | Partial | No area filter in code; tax topics appear in the documents |
| RNF10 | Traceability | High | Partial | [Matrix](traceability.md) updated in each PR |
| RNF11 | Version control | Critical | Implemented | Git and GitHub |
| RNF12 | Indicator documentation | High | Documented; acceptance pending | [Indicator guide](../architecture/indicators.md): purpose, definition, formula, population, source, labeled synthetic examples, limitations and traceability; Product Owner review pending |
| RNF13 | LGPD compliance | Critical | Implemented | Gold recipes and dashboard queries exclude `nivel_sigilo > 0` (TC-GLD-011, TC-GLD-012, TC-GLD-013) |
| RNF14 | Minimum sample | High | Partial | The new indicators require 30 decisions **with a result** for adequate reliability; `topic_results` still cuts on 30 closed cases |
