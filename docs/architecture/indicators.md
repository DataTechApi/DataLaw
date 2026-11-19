# Indicators — Business Rules and Traceability

This guide describes the product metrics implemented in DataLaw: what they
measure, how they are calculated and which evidence supports their behavior.
Requirements and verification gaps are linked in the
[traceability matrix](../requirements/traceability.md#indicator-rules-and-verification).
Implementation, automated verification and client validation are separate states.

All worked examples use **synthetic inputs**, not production observations.
A **test scenario** label means the inputs and expected result occur in an
existing automated test; it does not mean the repository query was exercised.
An **illustrative calculation** explains a rule without claiming an automated
database test for those inputs. Test IDs refer to the
[test catalog](../testing/test-cases.md); execution results belong in test reports.

## Shared data and calculation rules

The analytical recipes read Silver and materialize Gold tables. The
[Gold guide](gold.md) describes the materialization contract. Dashboard volumes
read Silver directly; the [code guide](../code/code-guide.md#key-business-rules)
describes the application rules and endpoints.

For the Gold outcome calculations:

- a closed case has code 22 or 246 as its latest dated movement;
- timestamp ties use the highest movement identifier;
- the result is the latest movement 219, 220 or 221 dated on or before closure;
- a closed case without that result contributes to closed cases E, but not
  to decisions with a result D;
- `COALESCE(nivel_sigilo, 0) = 0` excludes confidential cases and treats a null
  confidentiality level as public.

The Adherence Index additionally links cases and precedents by exact TPU
subject code and requires a curated direction (`autor` or `reu`).

| Selected result | Claim outcome | Thesis direction `autor` | Thesis direction `reu` |
|---|---|---|---|
| 219 | Granted | Adherent | Non-adherent |
| 220 | Denied | Non-adherent | Adherent |
| 221 | Partially granted | Partial | Partial |

The Java percentage and coverage methods use two decimal places and `HALF_UP`.
Gold recipes and native rate queries use PostgreSQL numeric `ROUND(..., 2)`.
Aggregated percentages are calculated from summed counts, not simple averages
of group percentages. A process can belong to multiple subjects or theses;
sums across those groups do not guarantee distinct cases.

## Adherence Index

**Purpose.** Estimate how often observed claim outcomes align with a curated
thesis direction in a selected subject.

**Definition and formula.** A is adherent decisions, P partial decisions,
N non-adherent decisions and D = A + P + N.
**Adherence Index (%) = 100 × (A + 0.5 × P) / D.**

**Population and filters.** Apply the shared Gold rules, exact TPU association
and curated direction. Missing or `indefinida` directions are excluded.
Gold groups by court, judging body, subject and precedent. The dashboard uses
a case-insensitive partial subject-name match (`ILIKE`), keeps theses separate
and displays the main thesis. Its class filter does not apply to this index.

**Data source and implementation.**
[topic_adherence.py](../../backend/src/data_law/infra/database/model/gold/topic_adherence.py)
reads `silver.processo`, `silver.processo_assunto`, `silver.movimento`,
`silver.jurisprudencia` and `silver.precedente_direcao`, producing counts and
`indice_adesao_pct` in `gold.topic_adherence`.
[ProcessoRepository.java](../../frontend/src/main/java/com/datatech/datalaw/repository/ProcessoRepository.java)
(`findAdesaoPorTese`) sums `aderentes`, `parciais`, `nao_aderentes` and
`decisoes_com_resultado`.
[ProcessoService.java](../../frontend/src/main/java/com/datatech/datalaw/service/ProcessoService.java)
(`indicadorAdesao`, `percentual`) calculates the displayed index.

**Worked example — test scenario.** A = 6, P = 2, N = 2 and D = 10 give
100 × (6 + 0.5 × 2) / 10 = **70.00%** (TC-FE-SVC-012, mocked repository).
For the opposite thesis direction, the same outcomes give A = 2, P = 2,
N = 6 and an index of **30.00%** (TC-GLD-013, PostgreSQL integration scenario).

**Limitations and validation.** This is a proxy based on claim outcomes and
curated direction; it does not check the decision text for actual application
of the precedent. It is not an individual probability of success. D = 0 gives
`null`; D > 0 with A = P = 0 gives a real 0%. Without a curated thesis the
index is `null`. Client approval of the 0.5 partial weight remains pending.

**Traceability.** RF09, RF10 and RF11; TC-GLD-010 (recipe inspection),
TC-GLD-013/014 (database classification and null result), TC-FE-SVC-007/008/012/013
(service calculation and missing data). Legal curation remains pending (RF10).

## Coverage

**Purpose.** Show how much of the closed-case population contributes a
classifiable result to the selected thesis index.

**Definition and formula.** D is decisions with a result and E is closed cases
for the same thesis and scope. **Coverage (%) = 100 × D / E.**

**Population and filters.** Use the main thesis and subject scope of the
Adherence Index. Closed cases without a result remain in E.

**Data source and implementation.** `gold.topic_adherence.decisoes_com_resultado`
and `processos_encerrados` supply the counts through `findAdesaoPorTese`;
`ProcessoService.indicadorAdesao` calls `cobertura`.

**Worked example — test scenario.** D = 10 and E = 20 give
100 × 10 / 20 = **50.00%** (TC-FE-SVC-012, mocked repository).

**Limitations and validation.** Coverage measures available classification,
not accuracy. E = 0 gives `null`; E > 0 with D = 0 gives 0%.
Without a curated thesis the dashboard returns `null` for coverage.
No client approval record is established by this guide.

**Traceability.** RF13; TC-FE-SVC-012 checks the example, TC-FE-SVC-008 checks
zero denominators and TC-FE-SVC-013 checks absence of a curated thesis.

## Sample size

**Purpose.** Expose the number of classified observations behind a percentage.

**Definition and formula.** For adherence, **D = A + P + N**. For party
outcomes, **D = granted + partially granted + denied claims**.
The unit is a classified closed case per subject/thesis scope, using one
selected result per case, not a count of every movement in its history.

**Population and filters.** Use the population of the associated indicator.
A sample is local to its thesis or group; E includes additional unclassified
closed cases and must not replace D.

**Data source and implementation.** `decisoes_com_resultado` in
`gold.topic_adherence` and `gold.topic_party_results`; repository sum queries
and `ProcessoService.indicadorAdesao`, `obterResultadoPorPolo` and `grupo`.

**Worked example — test scenario.** 60 granted + 20 partial + 20 denied =
**100 decisions with a result**, with E = 120 closed cases
(TC-FE-SVC-010, mocked repository).

**Limitations and validation.** Matching multiple subject names can count the
same process in more than one Gold group. D is not a guaranteed distinct
population across subjects or theses. Sample size alone does not establish
representativeness; no additional client approval is claimed here.

**Traceability.** RF08 and RF13; TC-FE-SVC-010/012 check samples in service
responses; TC-GLD-012/013 exercise the underlying Gold counts in PostgreSQL.

## Reliability

**Purpose.** Flag small samples before users interpret an outcome percentage.

**Definition and formula.** Reliability is a category derived from D:

| D: decisions with a result | Category |
|---|---|
| 0 | Insufficient data |
| 1 to 29 | Low |
| 30 or more | Adequate |

**Population and filters.** Apply the rule independently to the sample of
the selected thesis, each comparison group or the party view.

**Data source and implementation.**
[Confiabilidade.java](../../frontend/src/main/java/com/datatech/datalaw/entity/dto/Confiabilidade.java),
`AMOSTRA_MINIMA = 30` and `paraAmostra`; called by `ProcessoService`.

**Worked example — test scenario.** D = 0 gives insufficient data, D = 29
is low and D = 30 is adequate (TC-FE-SVC-009).

**Limitations and validation.** This rule provides no confidence interval or
statistical guarantee. The legacy subject rate instead filters on E >= 30;
that population cutoff is not equivalent to adequate reliability. RNF14
remains partial because these rules are not aligned. No client approval
record for the threshold is established here.

**Traceability.** RNF14 and RF13; TC-FE-SVC-009 tests category boundaries.

## Plaintiff and defendant percentages

**Purpose.** Show how claim outcomes split between the two parties,
independently of a particular precedent.

**Definition and formula.** G is granted claims (219), P partial claims (221),
R denied claims (220) and D = G + P + R.
**Plaintiff (%) = 100 × (G + 0.5 × P) / D.**
**Defendant (%) = 100 × (R + 0.5 × P) / D.**

**Population and filters.** Apply the shared Gold closure and confidentiality
rules. No curated direction is needed. Gold groups by court and TPU subject;
`findTotaisPorPolo` uses partial subject matching and sums the counts.
The class filter does not apply.

**Data source and implementation.**
[topic_party_results.py](../../backend/src/data_law/infra/database/model/gold/topic_party_results.py)
reads Silver processes, subjects and movements, producing `procedentes`,
`parciais`, `improcedentes`, `decisoes_com_resultado`, `processos_encerrados`,
`autor_pct` and `reu_pct` in `gold.topic_party_results`.
`ProcessoService.obterResultadoPorPolo` recalculates percentages from counts.

**Worked example — test scenario.** G = 60, P = 20, R = 20 and E = 120 give
D = 100, **70.00% plaintiff** and **30.00% defendant**. The other 20 closed
cases do not enter either denominator (TC-FE-SVC-010, mocked repository).

**Limitations and validation.** Both percentages are `null` when D = 0.
Partial claims contribute half to each side. Outcomes do not establish
adherence to a thesis. Client validation of the movement rule is pending (RF08).

**Traceability.** RF08; TC-GLD-009 inspects the recipe, TC-GLD-012 executes
its 6/2/2 database scenario, TC-FE-SVC-010/011 check service output.

## Weighted success rates by class and subject

**Purpose.** Summarize plaintiff outcomes for a procedural class or TPU subject.

**Definition and formula.** F is favorable outcomes (219), P partial outcomes
(221) and D all classified outcomes (219, 220 or 221).
**Weighted success rate (%) = 100 × (F + 0.5 × P) / D.**

**Population and filters.** Both use the shared Gold rules without curation:

| Indicator | Gold grouping | API filter | Population threshold |
|---|---|---|---|
| By class | Court, class code and name | Exact `classe_nome = classeNome`; no subject filter | None |
| By subject | Court, subject code and name | Exact `assunto_nome = assuntoNome`; no class filter | E >= 30 per Gold group |

**Data source and implementation.**
[process_results.py](../../backend/src/data_law/infra/database/model/gold/process_results.py)
and [topic_results.py](../../backend/src/data_law/infra/database/model/gold/topic_results.py)
read Silver processes and movements (plus subjects for the subject recipe).
Their Gold outputs include `favoraveis`, `parciais`, `desfavoraveis`,
`processos_com_resultado`, `processos_encerrados` and `taxa_sucesso_ponderada_pct`.
`ProcessoRepository.findTaxaSucessoPorClasse` and `findTaxaSucessoPorAssunto`
recalculate rates from summed counts for `/processos/taxa-sucesso` and
`/processos/taxa-sucesso-tema`.

**Worked examples — illustrative calculations, not database test fixtures.**
For one class, court A has F = 6, P = 2, D = 10; court B has
F = 1, P = 0, D = 2. The combined rate is
100 × (7 + 0.5 × 2) / 12 = **66.67%**, not the simple mean of 70% and 50%.
For one subject group, E = 30, F = 6, P = 2, D = 10 gives **70.00%**.
A group with E = 29 is excluded before aggregation across courts.

**Limitations and validation.** Missing data or D = 0 produces `null`.
The subject cutoff uses closed cases, so E = 30 with D = 10 passes the
cutoff despite a low sample under RNF14. Legacy endpoints expose no reliability
field. These are outcome rates, not curated-thesis adherence. Client approval
of the partial weight remains pending; illustrative examples are not approval.

**Traceability.** RF01/RF06 provide broad dashboard scope, not dedicated
acceptance criteria for each legacy query. TC-GLD-006/007 inspect recipe
registration and SQL; TC-FE-SVC-004/005 only check forwarding of mocked values.
Native repository SQL and the examples above lack database execution tests.

## Case volumes by judging body, class and subject

**Purpose.** Show where the stored public-case population is concentrated.

**Definition and formula.**
**Group volume = COUNT(DISTINCT processo.id) within that group and filters.**
The unit is a distinct case within a displayed name group.

**Population and filters.** Read Silver without an additional closure or
merit-result condition; require `COALESCE(nivel_sigilo, 0) = 0`.

| Volume | Optional filters using partial `ILIKE` | Excluded group names | Limit |
|---|---|---|---|
| By judging body | Class and subject | Null or empty body | Top 50 |
| By class | Subject only | Null or empty class | Top 50 |
| By subject | Class and subject | Null or empty subject | Top 25; at least 30 distinct cases per subject name |

Null or empty filter parameters disable that filter. Sort by volume descending.

**Data source and implementation.** `silver.processo.id`, `classe_nome`,
`orgao_julgador_nome`, `nivel_sigilo` and `silver.processo_assunto.nome`, joined
by process ID. `ProcessoRepository.findQuantidadeProcessosPorOrgaoJulgador`,
`findQuantidadeProcessosPorClasse` and `findQuantidadeProcessosPorAssunto`.

**Worked examples — illustrative calculations, not database test fixtures.**
Two public cases in the same body and class have three matching subject
associations between them: the body and class volumes are **2**, not 3.
A confidential case contributes nothing. For subject volumes, A with 30
distinct public cases qualifies; B with 29 does not.

**Limitations and validation.** Grouping by name can combine courts or codes.
A process can contribute once to several subject groups. Summing bars does
not guarantee a distinct total; display limits can omit groups. If no groups
qualify, the result is an empty list. These examples do not establish client approval.

**Traceability.** RF01/RF06 (broad dashboard scope); TC-FE-SVC-001/002/003
verify forwarding only. Native query counting and filtering lack database
execution tests in the current suite.

## Adherence comparisons by judging body and thesis

**Purpose.** Compare observed alignment across bodies for the same thesis,
and show separate results for different theses in a subject.

**Definition and formula.** For each group g,
**Index of g (%) = 100 × (A_g + 0.5 × P_g) / D_g**.
Each group also carries its own D and reliability category.

**Population and filters.** Use `gold.topic_adherence` and partial subject matching.

| Comparison | Group and additional filters | Order and limit |
|---|---|---|
| By body | Exact thesis ID; group by body name; omit null names and D = 0 | Highest index, then largest D; top 15 |
| By thesis | Group by precedent ID, metadata and direction | Highest index, then largest D; null indexes last; no service limit |

The class filter does not apply. The dashboard uses the main thesis for the
body comparison. Main-thesis selection prioritizes reliability, then largest
D, then highest index. `teseId` changes evidence selection only.

**Data source and implementation.** Gold columns `jurisprudencia_id`,
`orgao_julgador_nome`, `direcao`, `aderentes`, `parciais` and
`decisoes_com_resultado`; `ProcessoRepository.findAdesaoPorOrgao` /
`findAdesaoPorTese`; `ProcessoService.obterAdesaoPorOrgao`, `adesaoPorTese`,
`grupo` and `tesePrincipal`.

**Worked examples — test scenarios with mocked repository results.**
Body A with A = 9, P = 0, D = 10 has **90.00%**; body B with
A = 5, P = 0, D = 10 has **50.00%**. A ranks first; both have low
reliability (TC-FE-SVC-016).
Three theses with (A, P, D) of (2, 0, 2), (25, 2, 28) and (1, 2, 28)
have **100.00%**, **92.86%** and **7.14%**. They rank in that order,
but the second is the main thesis because of sample size and the index
tiebreaker (TC-FE-SVC-014).

**Limitations and validation.** Never pool opposite thesis directions into
one index. Body names can combine courts; the highest index need not have
adequate reliability or be the main thesis. Without curated theses,
comparison lists are empty. No client acceptance record is established here.

**Traceability.** RF11/RF12; TC-FE-SVC-014/015/016/017 verify service selection,
ranking, empty results and thesis metadata. TC-FE-SVC-019 verifies evidence
selection independently of the main thesis. Native comparison queries lack
database execution tests; Gold classification has TC-GLD-013.

## Evidence boundaries and acceptance

Service tests in
[ProcessoServiceTest.java](../../frontend/src/test/java/com/datatech/datalaw/service/ProcessoServiceTest.java)
mock repository output. Recipe-inspection tests in
[test_gold.py](../../backend/tests/transformation/test_gold.py)
inspect registration and SQL structure. Neither executes repository native SQL.
Gold integration tests in
[test_gold_indicators_integration.py](../../backend/tests/transformation/test_gold_indicators_integration.py)
seed synthetic cases in disposable PostgreSQL and exercise Gold recipes.

Existing tests demonstrate their stated scenarios, not complete business
acceptance. RF08 movement interpretation, RF10 legal curation and RF11 partial
weight have outstanding validation work. Documentation and traceability review
by the Product Owner remain pending. This guide establishes no release,
deployment, defect closure or client approval record; those must link actual
artifacts in the [traceability matrix](../requirements/traceability.md).
The [Product Owner review checklist](../requirements/traceability.md#product-owner-review)
identifies the business decisions and acceptance evidence still required.
