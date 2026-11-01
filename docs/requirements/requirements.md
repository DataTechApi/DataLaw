# Requirements Specification — DataLaw

Sprint 3 revision. IDs RF01–RF11 and RNF01–RNF11 were kept to preserve history.

## 1. Client definitions

These statements drive Sprint 3 priorities. They are translated from Portuguese; the original wording is kept below each one.

> Highest-value metric: Adherence Index (%) to the topic/precedent. It is the heart of Legal Analytics. Average time and archival rate are secondary and offer little strategic intelligence because their averages are widely known.

*Original: "Métrica de maior valor: Índice de Adesão (%) ao tema/precedente. É o coração do Legal Analytics. Tempo médio e taxa de arquivamento são secundários e trazem pouca inteligência estratégica pois são valores amplamente conhecidos na média."*

> Definition of a favorable decision: favorable to the researched thesis/topic (and/or the appeal being granted). The focus is whether the judgment accepted the legal position under analysis, regardless of plaintiff or defendant.

*Original: "Definição de decisão favorável: Favorável à tese/tema pesquisado (e/ou provimento do recurso). O foco é saber se o julgado acolheu a posição jurídica analisada, independentemente de ser autor ou réu."*

## 2. Glossary

| Term | Definition |
|---|---|
| Topic | Subject in the Unified Procedural Table (TPU) |
| Precedent | Qualified thesis from STJ, STF or TJs |
| Thesis direction | Party the thesis benefits: `plaintiff`, `defendant` or `undefined` |
| Decision with a result | Closed case with merit movement 219, 220 or 221 |
| Adherent decision | Decision whose result matches the thesis direction |
| Adherence Index | Percentage of adherent decisions among decisions with a result |

## 3. Functional requirements

### 3.1 Highest-value requirements (Sprint 3)

#### RF08 — Classify the decision against the thesis

- **Requested by:** client
- **Priority:** Critical
- **Status:** Planned
- **Description:** the system must classify each decision with a result as adherent, partially adherent or non-adherent to the analyzed thesis.
- **Acceptance criteria:**
  - Thesis favoring the plaintiff: movement 219 is adherent and 220 is non-adherent.
  - Thesis favoring the defendant: movement 220 is adherent and 219 is non-adherent.
  - Movement 221 is partially adherent in both directions.
  - A thesis with `undefined` direction is left out of the calculation.
  - A case without a merit movement stays out of the denominator.

#### RF09 — Record the thesis direction

- **Requested by:** team, to enable the client's definition
- **Priority:** Critical
- **Status:** Planned
- **Description:** each precedent used in the index must have its thesis direction recorded, with curator and date.
- **Reason:** the sampled DataJud payload has no decision text, and the BNP data in use does not state which party a thesis benefits.
- **Acceptance criteria:**
  - Direction accepts only `plaintiff`, `defendant` or `undefined`.
  - The record stores curator and date.
  - A precedent without curation is treated as `undefined`.

#### RF10 — Calculate the Adherence Index

- **Requested by:** client
- **Priority:** Critical
- **Status:** Planned
- **Description:** the system must calculate the Adherence Index by court, topic and precedent in the Gold layer.
- **Proposed formula:**

```text
Adherence Index (%) = 100 × (adherent + 0.5 × partial) / decisions with a result
```

- **Acceptance criteria:**
  - The formula is tested with closed scenarios in both thesis directions.
  - With no decisions with a result, the index is null, not 0%.
  - The client has validated the 0.5 weight for partial decisions (see P2).

#### RF11 — Display the Adherence Index as the main indicator

- **Requested by:** client
- **Priority:** High
- **Status:** Planned
- **Description:** when a topic is selected, the user must first see the Adherence Index and the comparison by judging body. Average time and archival stay secondary.
- **Acceptance criteria:**
  - The index has greater visual emphasis than secondary indicators.
  - The comparison sorts judging bodies by index.
  - A topic without data shows "Insufficient data", never 0%.

#### RF12 — Show indicator source and reliability

- **Requested by:** client (story 1.4)
- **Priority:** High
- **Status:** Planned
- **Description:** the index must show source, update date, sample size and coverage.
- **Acceptance criteria:**
  - Shows the totals of decisions with a result and closed cases.
  - Shows coverage: decisions with a result ÷ closed cases.
  - A sample below the RNF14 minimum shows a low-reliability warning.

#### RF13 — Display the evidence behind the index

- **Requested by:** client (story 3.5)
- **Priority:** High
- **Status:** Planned
- **Description:** from the index, the user must be able to open the cases and the precedent that support the calculation.
- **Acceptance criteria:**
  - Lists case number, judging body, movement, date and classification.
  - Shows the thesis and direction used in the calculation.
  - The list totals match the value shown in the indicator.
  - No case with `nivel_sigilo > 0` appears.

#### RF14 — Display the view by party

- **Requested by:** Product Owner, pending client validation
- **Priority:** Medium
- **Status:** Conditional (see P1)
- **Description:** the system may show how results split between plaintiff and defendant in the selected topic.
- **Proposed rule:** movement 219 favors the plaintiff, 220 favors the defendant and 221 is partial. The calculation does not need to identify the parties.
- **Acceptance criterion:** the view is a complement and does not replace the Adherence Index.

### 3.2 Revised original requirements

| ID | Requirement | Priority | Status | Current code |
|---|---|---|---|---|
| RF01 | Single-screen metrics | High | Partial | Volumes and a rate in a modal; adherence comes through RF11 |
| RF02 | DataJud extraction | Critical | Implemented | Only TJSP is configured |
| RF03 | Open data extraction | High | Partial | BNP integration exists |
| RF04 | Cleaning and standardization | Critical | Implemented | Bronze and Silver layers |
| RF05 | Dimensional storage | High | Partial | Aggregated Gold tables exist; no fact and dimension tables |
| RF06 | Indicator dashboards | High | Partial | Volume dashboard exists; processing time is not displayed |
| RF07 | Outcome classification | Critical | Partial | Claim outcome is classified; adherence is detailed in RF08 |

## 4. Non-functional requirements

| ID | Requirement | Priority | Status | Verification |
|---|---|---|---|---|
| RNF01 | Data model documentation | Medium | Partial | Dictionary in `docs/architecture/data-dictionary.md` |
| RNF02 | API documentation | Medium | Partial | [Code guide](../code/code-guide.md) lists the endpoints |
| RNF03 | Backend in Python | Critical | Implemented | `backend/` |
| RNF04 | Frontend in Java | Critical | Implemented | `frontend/` |
| RNF05 | Unit and integration tests | High | Partial | Unit suites exist; integration coverage of queries is pending |
| RNF06 | Functional tests | Medium | Partial | Controller tests exist; no UI tests |
| RNF07 | Continuous static analysis | Medium | Partial | `ruff` runs in CI; `mypy` is manual; no SonarQube configuration in the repository |
| RNF08 | CI/CD | High | Implemented | `.github/workflows/deploy.yml` |
| RNF09 | Civil law scope | High | Partial | No area filter in code; tax topics appear in the documents (see P5) |
| RNF10 | Traceability | High | Partial | [Matrix](traceability.md) updated in each PR |
| RNF11 | Version control | Critical | Implemented | Git and GitHub |
| RNF12 | Indicator documentation | High | Planned | Formula, assumptions and example for each indicator |
| RNF13 | LGPD compliance | Critical | Partial | Gold and screens exclude `nivel_sigilo > 0`, verified by test |
| RNF14 | Minimum sample | High | Partial | Index requires 30 decisions **with a result**; the current cut uses closed cases |
