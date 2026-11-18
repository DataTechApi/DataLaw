# Indicators — Adherence Index

This first increment of US3.5 / SCRUM-142 documents the implemented Adherence
Index, coverage and reliability. The examples use synthetic data.
The weight of 0.5 for partial decisions still requires client validation,
as recorded in [RF11](../requirements/requirements.md#rf11--calculate-the-adherence-index).

## Data source and calculation population

The [topic_adherence.py](../../backend/src/data_law/infra/database/model/gold/topic_adherence.py)
recipe materializes `gold.topic_adherence` from Silver. Each row groups cases
by court, judging body, TPU subject and precedent with a curated direction
(`autor` for plaintiff or `reu` for defendant).

A case enters the population when:

- its latest dated movement has code 22 or 246; timestamp ties are resolved
  using the highest movement identifier;
- `COALESCE(nivel_sigilo, 0) = 0`;
- its TPU subject matches the subject of the curated precedent.

To classify the outcome, the recipe selects the latest movement with code
219, 220 or 221 dated on or before closure. Ties also use the highest movement
identifier. Without such a movement, the case counts as closed but is excluded
from decisions with a result. Precedents without a curated direction or with
an `indefinida` (undefined) direction are excluded from the index.

| Selected movement | Direction `autor` | Direction `reu` |
|---|---|---|
| 219 — Claim granted | Adherent | Non-adherent |
| 220 — Claim denied | Non-adherent | Adherent |
| 221 — Claim partially granted | Partial | Partial |

Classification combines the claim outcome, TPU subject and curated direction.
It does not check the decision text to establish whether the judge applied
the precedent.

## Formulas and reproducible example

For the same thesis and scope, let:

- **A:** adherent decisions;
- **P:** partial decisions;
- **N:** non-adherent decisions;
- **D = A + P + N:** decisions with a result;
- **E:** closed cases, including those without a classifiable result.

**Adherence Index (%) = 100 × (A + 0.5 × P) / D.**

**Coverage (%) = 100 × D / E.**

Example: 20 closed cases, including 6 adherent, 2 partial,
2 non-adherent and 10 without a classifiable result:

| Measure | Substitution | Result |
|---|---|---|
| Decisions with a result | 6 + 2 + 2 | 10 |
| Adherence Index | 100 × (6 + 0.5 × 2) / 10 | 70.00% |
| Coverage | 100 × 10 / 20 | 50.00% |
| Reliability | 10 decisions with a result | Low |

If the same outcomes are compared against a thesis with the opposite direction,
the 6 adherent decisions become non-adherent and the 2 non-adherent decisions
become adherent. The index for that other thesis is
100 × (2 + 0.5 × 2) / 10 = **30.00%**.
The two theses are calculated separately.

The index is `null` when D = 0; coverage is `null` when E = 0.
With E > 0 and D = 0, coverage is 0.00% and the index remains `null`.
With D > 0 and A = P = 0, the index is actually 0.00%.
Without a curated thesis, the dashboard returns `null` for both index and coverage.

Percentages are rounded to two decimal places. The Java service uses
`HALF_UP`: for example, 100 × 1 / 3 yields 33.33%.

## Reliability and presentation

The rule in [Confiabilidade.java](../../frontend/src/main/java/com/datatech/datalaw/entity/dto/Confiabilidade.java)
uses D rather than E:

| Decisions with a result | Classification |
|---|---|
| 0 | Insufficient data |
| 1 to 29 | Low |
| 30 or more | Adequate |

This is a sample-size rule. It does not calculate a confidence interval
or provide a statistical guarantee of representativeness.

[ProcessoService.java](../../frontend/src/main/java/com/datatech/datalaw/service/ProcessoService.java)
recalculates the index from summed counts, keeping each thesis separate;
it does not take a simple average of group percentages. The dashboard selects
the main thesis by reliability, then largest D, then highest index.
Without a curated thesis, it displays insufficient data.

The dashboard subject filter uses case-insensitive partial matching (`ILIKE`).
A case may contribute to more than one subject or thesis: sums across subjects
do not guarantee distinct cases. The index describes the observed scope;
it is not an individual probability of success in a new case.

## Tests supporting the example

- [ProcessoServiceTest.java](../../frontend/src/test/java/com/datatech/datalaw/service/ProcessoServiceTest.java):
  `indicadorAdesaoCalculaIndiceCoberturaEConfiabilidade` checks the
  6/2/2 scenario, E = 20, a 70% index, 50% coverage and low reliability;
  `percentualSemDecisoesEhNuloENaoZero` checks zero denominators;
  `confiabilidadeDependeDaAmostraMinima` checks D = 0, 29 and 30.
- [test_gold_indicators_integration.py](../../backend/tests/transformation/test_gold_indicators_integration.py):
  `test_topic_adherence_classifies_by_thesis_direction` checks the
  70% and 30% indexes for opposite directions;
  `test_topic_adherence_is_null_without_decisions_with_a_result` checks
  a null index without a result. These tests require a disposable PostgreSQL database.

The remaining indicators and the traceability matrix update belong to
subsequent increments. Client validation remains pending.
