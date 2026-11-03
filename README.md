<div align="center">

# DATALAW
### 5th Semester — Database Technology (Fatec SJC)
#### Partner: Xertica

</div>

<p align="center">
  <a href="#busts_in_silhouette-team-members">Team Members</a> •
  <a href="#pushpin-datalaw-project">DataLaw Project</a> •
  <a href="#white_check_mark-requirements">Requirements</a> •
  <a href="#card_file_box-product-backlog">Product Backlog</a> •
  <a href="#calendar-sprint-backlog">Sprint Backlog</a> •
  <a href="#hourglass_flowing_sand-project-timeline">Timeline</a> •
  <a href="#computer-technologies-used">Technologies Used</a> •
  <a href="#gear-branching-strategy">Branching Strategy</a> •
  <a href="#gear-sonarqube">SonarQube</a> •
  <a href="#gear-documentation">Documentation</a>
</p>

<h1 align="center" id="busts_in_silhouette-team-members">Team Members</h1>

<div align="center">

| Member | Role |
|---|---|
| Cauê Gandini | Product Owner |
| Jackson Moraes | Scrum Master |
| Cleber Kirch | Developer |
| Davi Gramacho | Developer |
| Pablo Lima | Developer |

</div>

<br>

<h1 id="pushpin-datalaw-project">📌 DataLaw Project</h1>

## **Challenge**

<p align="justify">
Legal professionals (lawyers and judges) face a critical problem: legal data — case law, precedents (STF, STJ, TJ) and legal doctrine — is scattered across multiple formats and incompatible systems. This makes it slow, confusing and costly to search for information and build well-founded legal arguments.
</p>

<p align="justify">
After an initial discovery round, a deeper round of stakeholder interviews revealed a more precise pain point: legal, compliance and judicial decision-makers do not lack access to legal data — they lack <b>reliable indicators of trend, predictability and volume</b> to support high-impact decisions such as financial risk provisioning, settlement vs. litigation choices, and case backlog management. Centralizing the data was necessary, but not sufficient — the real value lies in turning dispersed decisions into decision-ready metrics.
</p>

The challenge required the team to:
- Design and implement a **Data Warehouse architecture** integrating multiple legal data sources;
- Build **ETL pipelines** to extract, clean and load unstructured legal data;
- Apply **dimensional modeling** techniques to organize facts (decisions/cases) and dimensions (topics, courts, authors, periods);
- Enable **OLAP analysis** to reveal jurisprudence patterns and doctrinal correlations;
- Apply **DevOps best practices**, with automated testing to ensure data integrity and query consistency.

## **Solution — DataLaw**

<p align="justify">
DataLaw is a Business Intelligence platform applied to Law. It consolidates case law, precedents and legal doctrine into a single dimensional model, and turns them into actionable indicators of adherence, processing time and volume — answering business questions directly (e.g. <i>"Which court has the highest adherence to Topic X of General Repercussion?"</i>) rather than only returning a list of documents.
</p>

DataLaw focuses on minimalism and clarity. Our solution delivers decision-ready metrics in one or two screens, with intuitive navigation and natural language queries.

- Single-screen interface: Adherence rate, average processing time, and case volume displayed in one place.
- Natural language queries: Users ask questions directly (e.g., “Which court has the highest adherence to Topic X?”) and receive metrics, not just documents.
- Transparency: Every metric is accompanied by its original source and a reliability indicator.

**Target users:**
- **Legal Managers / Legal Ops / Executives** — evaluate success rates of legal theses and average processing time to support financial decisions (risk provisioning, settle vs. litigate).
- **Strategic Lawyers** — identify the prevailing position of courts on emerging legal theses and estimate the probability of success before filing an action or appeal.
- **Judges / Judicial Analysts** — track volume and adherence to binding precedents (STF/STJ) to manage stalled or pending case backlogs.

**Scope:** STF (constitutional matters), STJ (unifying precedents) and TJ (state-level case law) — restricted exclusively to **civil law** across all three instances.
<br>

## **Running Locally**
### **Prerequisites**

- Git
- [uv](https://docs.astral.sh/uv/)
- A [DataJud](https://datajud-wiki.cnj.jus.br/api-publica/acesso/) Public API access key

### Installation
```bash
git clone <REPOSITORY_URL>
cd DataLaw
uv sync
```

### API Key Configuration

Create a `.env` file in the project root:

```env
DATAJUD_API_KEY=your_api_key
```

### Run the Ingestion

```bash
uv run python -m data_law.main
```

The application queries TJSP cases with a final dismissal or definitive archival movement in the past six months.

Raw API responses are automatically saved to:

```text
data/raw/tjsp/
```
### Code Quality

```bash
uv run ruff format src tests
uv run ruff check src tests
```

</details>

<br>

<h1 id="card_file_box-product-backlog">🗂 Product Backlog</h1>


| Rank | Priority | User Story | Points | Sprint |
| --- | --- | --- | --- | --- |
| 1.1 | Critical | As a Strategic Lawyer, I want to filter decisions by court and period, so that I can quickly locate relevant jurisprudence for my case. | 8 | 1 |
| 1.2 | High | As a Strategic Lawyer, I want to consult decisions from STJ, STF, and State Courts already cleaned and standardized, so that I reduce the time spent gathering jurisprudence from different sources. | 5 | 1 |
| 1.3 | High | As a Lawyer/Judge, I want to search and visualize real decisions in a simple way, so that I can validate that the system already provides useful data from the start. | 5 | 1 |
| 1.4 | High | As the system, I need to display the original source and a reliability indicator for each result, so that transparency is ensured for the user. | 3 | 1 |
| 1.5 | Medium | As a Legal Manager, I want the data structure and API of the platform to be well documented and traceable from the beginning, so that I can trust the numbers used in financial decisions. | 3 | 1 |
| 2.1 | High | As a Legal Manager, I want to analyze case volume across multiple courts, so that I can identify where a legal topic is most concentrated. | 5 | 2 |
| 2.2 | High | As a Legal Manager, I want to view the average case processing time by court and legal topic, so that I can evaluate judicial efficiency. | 5 | 2 |
| 2.3 | High | As a Strategic Lawyer, I want to view the courts with the highest concentration of a topic, so that I can identify regional legal trends. | 3 | 2 |
| 2.4 | High | As a Strategic Lawyer, I want to view the evolution of a legal topic over time, so that I can identify growth or reduction patterns. | 5 | 2 |
| 2.5 | High | As a Legal Manager, I want to view adherence indicators for a selected topic, so that I can evaluate how strongly the topic appears within the analyzed dataset. | 8 | 2 |
| 2.8 | High | As a Strategic Lawyer, I want to access related jurisprudence references for a searched topic, so that I can deepen my legal research. | 5 | 2 |
| 2.9 | Medium | As a User, I want dashboards to display data source and reliability information, so that I can trust the generated indicators. | 3 | 2 |
| 3.1 | High | As a Strategic Lawyer, I want each decision classified as adherent or non-adherent to the analyzed thesis, regardless of plaintiff or defendant, so that the result reflects whether the court accepted the legal position. | 5 | 3 |
| 3.2 | High | As a Legal Manager, I want the Adherence Index (%) by topic and precedent, so that I can base risk and litigation decisions on the platform's main metric. | 5 | 3 |
| 3.3 | High | As a Strategic Lawyer, I want the Adherence Index as the main dashboard indicator, with sample size and reliability, compared by judging body, so that I can assess where a thesis is accepted. | 3 | 3 |
| 3.4 | High | As a Legal Manager, I want evidence linked to the Adherence Index, so that I can verify how the result was calculated. | 3 | 3 |
| 3.5 | Medium | As a Legal Manager, I want complete documentation of indicators, calculations and requirements traceability, so that I can trust the platform results. | 3 | 3 |

### **Global Definition of Done (DoD)**

A backlog item is considered done if:

* Code has been written, tested locally and follows the team's code standards.
* Reviewed and approved by peers.
* Merged into the main integration branch.
* Automated tests created and passing.
* Acceptance criteria met.
* The computed indicator has been validated against the client's own reference numbers.
* The Product Owner has approved the functionality.

<br>

<h1 id="calendar-sprint-backlog">📅 Sprint Backlog</h1>

<details>
  <summary><b>Sprint 1</b></summary>

### **Sprint 1: Planning and Execution**

* **Sprint Goal:** Prove the core value proposition end to end — extract real decisions for one pilot court and topic, calculate one trustworthy business indicator (adherence rate), and display it with full source traceability. This validates the actual pain point identified with the client, rather than delivering a generic search screen.
* **Estimated Capacity:** 36 story points
* **Blocking dependency:** the business rule for what counts as "adherence"/"success" must be confirmed with the client before Story 1.4 can be reliably estimated and started.

| Rank | Priority | User Story | Points |
| --- | --- | --- | --- |
| 1.1 | Critical | Extract decisions from the DataJud (CNJ) API for a pilot court | 8 |
| 1.2 | Critical | Clean and standardize the extracted decisions | 5 |
| 1.3 | Critical | Build a minimal dimensional model (Fact + Court, Topic, Period, Outcome) | 5 |
| 1.4 | Critical | Calculate the adherence rate for one pilot legal topic | 8 |
| 1.5 | High | Display source and reliability indicator next to the pilot metric | 3 |
| 1.6 | High | Build a simple query interface to view supporting decisions | 3 |
| 1.7 | Medium | Document the initial data model and dictionary | 3 |
| 1.8 | Medium | Set up Jira project and traceability structure | 1 |

<details>
  
<summary><strong>US1.1 — Extract decisions from the DataJud (CNJ) API for a pilot court</strong></summary>

DoR Checklist

- Business rules defined: which court and decision types to extract.

- Data available: API access key configured and validated.

- Prototype approved: initial data ingestion flow documented.

</details>

<details>
<summary><strong>US1.2 — Clean and standardize the extracted decisions</strong></summary>

DoR Checklist

- Business rules defined: cleaning rules documented (remove duplicates, normalize fields).

- Data available: raw dataset ready for cleaning.

- Prototype approved: schema for cleaned dataset validated.


</details>

<details>
<summary><strong>US1.3 — Build a minimal dimensional model (Fact + Court, Topic, Period, Outcome)</strong></summary>

DoR Checklist

- Business rules defined: fact table and dimensions documented.

- Data available: cleaned dataset mapped to dimensional schema.

- Prototype approved: ER diagram or schema mockup available.

</details>

<details>
<summary><strong>US1.4 — Calculate the adherence rate for one pilot legal topic</strong></summary>

DoR Checklist

- Business rules defined: adherence calculation formula agreed with stakeholders.

- Data available: pilot dataset with topic classification.

- Prototype approved: metric displayed in single-screen interface.

</details>

<details>
<summary><strong>US1.5 — Display source and reliability indicator next to the pilot metric</strong></summary>

DoR Checklist

- Business rules defined: reliability calculation method documented.

- Data available: metadata accessible for each decision.

- Prototype approved: source and reliability displayed next to metrics.

</details>

<details>
<summary><strong>US1.6 — Build a simple query interface to view supporting decisions</strong></summary>

DoR Checklist

- Business rules defined: query parameters documented (court, topic, period).

- Data available: pilot dataset indexed for queries.

- Messages defined: error if query returns no results; success confirmation when decisions are displayed.

- Prototype approved: query interface mockup validated.

</details>

<details>
<summary><strong>US1.7 — Document the initial data model and dictionary</strong></summary>

DoR Checklist

- Business rules defined: documentation template agreed.

- Data available: dimensional schema finalized.

- Messages defined: documentation must include validation notes.

- Prototype approved: draft data dictionary reviewed.

</details>

<details>
<summary><strong>US1.8 — Set up Jira project and traceability structure</strong></summary>

DoR Checklist

- Business rules defined: backlog structure mapped to requirements.

- Data available: Jira project created with access for all team members.

- Messages defined: notifications configured for backlog changes.

- Prototype approved: Jira board structure validated.

</details>

</details>

<details>
  <summary><b>Sprint 2</b></summary>

### **Sprint 2: Planning and Execution**

* **Sprint Goal:** Expand DataLaw from a volumetric judicial dashboard into a legal intelligence platform by increasing court coverage, introducing analytical metrics and providing the first jurisprudence-based insights.
* **Estimated Capacity:** 29 story points

| Rank | Priority | User Story | Points |
| --- | --- | --- | --- |
| 2.1 | Highest | As a user, I want to view a Topic Adherence Indicator. | 5 |
| 2.2 | Highest | As a user, I want to access Topic-Related Jurisprudence. | 5 | 
| 2.3 | High | As a user, I want to view Precedent Associations. | 3 |
| 2.4 | High | As a user, I want to access Doctrine References. | 5 |
| 2.5 | Medium | As a user, I want to analyze data from an Expanded Set of Courts. | 3 | 
| 2.6 | High | As a user, I want to view Case Volume by Court. | 5 | 
| 2.7 | Medium | As a user, I want to view the Average Case Processing Time. | 3 | 

<details>
  
<summary><strong>US2.1 — Topic Adherence Indicator</strong></summary>
 
DoR Checklist

- Business rules defined: adherence calculation criteria and indicator thresholds documented.
 
- Data available: legal topic datasets validated and available in the warehouse
 
- Prototype approved: adherence indicator visualization defined.
 
</details>
 
<details>
<summary><strong>US2.2 — Topic-Related Jurisprudence</strong></summary>
 
DoR Checklist
  
- Business rules defined: jurisprudence retrieval and association criteria documented.
 
- Data available: jurisprudence database validated and accessible.
 
- Prototype approved: jurisprudence reference listing and navigation defined.
 
</details>
 
<details>
<summary><strong>US2.3 — Precedent Associations</strong></summary>
 
DoR Checklist

- Business rules defined: precedent association criteria and relevance rules documented.
 
- Data available: precedent datasets validated and available in the warehouse.
 
- Prototype approved: precedent association visualization defined.
 
</details>
 
<details>
<summary><strong>US2.4 — Doctrine References</strong></summary>
 
DoR Checklist
  
- Business rules defined: doctrine reference retrieval and classification criteria documented

- Data available: doctrinal reference datasets validated and available.

- Prototype approved: doctrine reference presentation defined.

</details>
 
<details>
<summary><strong>US2.5 — Expanded Set of Courts</strong></summary>
 
DoR Checklist
  
- Business rules defined: court inclusion criteria and scope documented.
 
- Data available: additional court datasets validated and available in the warehouse.
 
- Prototype approved: multi-court analysis interface defined.
 
</details>
 
<details>
<summary><strong>US2.6 — Case Volume by Court</strong></summary>
 
DoR Checklist
  
- Business rules defined: court aggregation and case counting criteria documented.
 
- Data available: court case datasets validated and available in the warehouse.
 
- Prototype approved: case volume visualization by court defined.

</details>
 
<details>
<summary><strong>US2.7 — Average Case Processing Time</strong></summary>
 
DoR Checklist
  
- Business rules defined: processing time calculation methodology documented.
 
- Data available: case lifecycle dates validated and available in the warehouse.
 
- Prototype approved: average processing time dashboard visualization defined.

</details>

</details>

<details>
  <summary><b>Sprint 3</b></summary>

### **Sprint 3: Planning and Execution**

* **Sprint Goal:** Deliver a reliable, traceable Adherence Index (%) by topic and precedent, the metric the client identified as the core of Legal Analytics.
* **Estimated Capacity:** 19 story points
* **Client definition:** a decision is favorable when it accepts the analyzed thesis, regardless of plaintiff or defendant. Average time and archival rate are secondary.
* **Blocking dependency:** the open decisions in [docs/requirements/open-items.md](docs/requirements/open-items.md) must be validated with the client.
* **Requirements and traceability:** see [docs/requirements](docs/requirements/README.md).

| Rank | Priority | User Story | Requirements | Use Case | Points |
| --- | --- | --- | --- | --- | --- |
| 3.1 | High | Classify decisions in relation to the thesis | RF09, RF10 | UC-01 | 5 |
| 3.2 | High | Calculate the Adherence Index | RF11, RNF13, RNF14 | UC-02 | 5 |
| 3.3 | Highest | Display the index with reliability, view by party and comparison by judging body | RF08, RF12, RF13 | UC-03, UC-06 | 3 |
| 3.4 | Medium | Provide evidence linked to the index | RF14, RNF13 | UC-04 | 3 |
| 3.5 | Low | Document indicators and traceability | RNF10, RNF12 | UC-05 | 3 |
| 3.6 | Highest | Compare plaintiff and defendant results by topic | RF08 | UC-06 | 1 |

<details>

<summary><strong>US3.1 — Classify decisions in relation to the thesis</strong></summary>

DoR Checklist

- Business rules defined: classification by thesis direction validated with the client.

- Data available: thesis direction registered for the pilot precedents.

- Prototype approved: classification rules reviewed by the Product Owner.

</details>

<details>

<summary><strong>US3.2 — Calculate the Adherence Index</strong></summary>

DoR Checklist

- Business rules defined: formula, partial decision weight and minimum sample documented.

- Data available: classified decisions available in the Gold layer.

- Prototype approved: expected result defined from a closed numeric example.

</details>

<details>

<summary><strong>US3.3 — Display the index with reliability and comparison by judging body</strong></summary>

DoR Checklist

- Business rules defined: reliability levels and insufficient-data behavior documented.

- Data available: Adherence Index available by judging body.

- Prototype approved: dashboard layout reviewed by the Product Owner.

</details>

<details>

<summary><strong>US3.4 — Provide evidence linked to the index</strong></summary>

DoR Checklist

- Business rules defined: evidence fields and LGPD exclusions documented.

- Data available: decisions and precedents used in the calculation accessible.

- Prototype approved: evidence section layout reviewed and approved.

</details>

<details>

<summary><strong>US3.5 — Document indicators and traceability</strong></summary>

DoR Checklist

- Business rules defined: formulas, assumptions and calculation methods documented.

- Data available: final indicators validated by the Product Owner.

- Prototype approved: documentation structure reviewed and approved.

</details>
<details>

<summary><strong>US3.6 — Compare plaintiff and defendant results by topic</strong></summary>

DoR Checklist

- Business rules defined: movement 219 counts for the plaintiff, 220 for the defendant and 221 as partial, validated with the client.

- Data available: merit movements of closed cases available in the Gold layer.

- Prototype approved: plaintiff and defendant view placed next to the Adherence Index on the dashboard.

</details>
</details>

<br>

<h1 id="hourglass_flowing_sand-project-timeline">⏳ Project Timeline</h1>

- - Kick-off with partner (Xertica)
- - Discovery follow-up: additional stakeholder questions to refine the real business pain point
- - Sprint 1 — Planning
- - Sprint 1 — Execution
- - Sprint 1 — Review / Sprint 2 Planning
- - Sprint 2 — Execution
- [-] Sprint 2 — Review / Sprint 3 Planning
- [ ] Sprint 3 — Execution
- [ ] Sprint 3 — Review
- [ ] Final presentation

<br>

<h1 id="computer-technologies-used">💻 Technologies Used</h1>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-green?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-🗄️-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-🐳-2496ED?logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-🌱-F05032?logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-000000?logo=github&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)
![Jira](https://img.shields.io/badge/Jira-0052CC?logo=jira&logoColor=white)
![VS Code](https://img.shields.io/badge/VS_Code-007ACC?logo=visualstudiocode&logoColor=white)
![SonarQube](https://img.shields.io/badge/SonarQube-4E9BCD?logo=sonarqube&logoColor=white)

</div>

**Notes on tooling choices:**
- **Python** - Mature ecosystem with robust ORMs (e.g., SQLAlchemy, Django ORM), excellent support for APIs (FastAPI, Flask), and strong libraries for data processing and NLP.
- **PostgreSQL** - Open-source RDBMS optimized for analytical workloads, supports advanced indexing (GIN, GiST), full-text search, and extensions like PostGIS. - Store and query large volumes of legal decisions efficiently, enabling OLAP-style analysis and semantic search. 
- **NLP (Pangea)** - Market reference cited by the partner; offers pretrained models for topic classification and entity extraction. Flexible integration with Python pipelines.
- **SonarQube** - Continuous static code analysis, detects vulnerabilities, code smells, and enforces quality gates. Integrates with CI/CD pipelines. - Guarantee code quality and compliance with Fatec’s explicit requirement for maintainable and secure software.
- **Docker + GitHub Actions** - Docker ensures reproducible environments; GitHub Actions automates builds, tests, and deployments. Together they enable CI/CD pipelines with minimal overhead. 
- **Jira** - Native mapping to agile workflows, supports backlog management, sprint planning, and traceability from requirements to delivery. - Ensure full visibility of progress and alignment with the team’s workflow (Problem → Solution Proposal → Requirements → MVP → Backlog → DoR → Sprint Backlog → Version Control). 
- **VS Code** - Lightweight IDE, cross-platform, with extensive extensions for Python, Docker, GitHub, and PostgreSQL. Highly customizable and resource-efficient.

<br>

<h1 id="gear-branching-strategy">🌿 Branching Strategy and Commit Pattern</h1>

<details>
  <summary><b>Branching Strategy</b></summary>

**Typical workflow:**
1. Create a **sprint branch** from `main`.
2. Develop the functionality..
3. Open a **Pull Request** to `main`.
4. After the required approvals, merge into `main`.

</details>

<details>
  <summary><b>Commit and Branch Naming Pattern</b></summary>

All commit content is written in **lowercase**, except for the **Task ID**. Commits should be small and frequent, each one traceable to a task.

**Example:**
```
git commit -m "SCRUM-1 feat(etl): add datajud extraction client"
```

| Type | Description | Example |
|---|---|---|
| :sparkles: feat | New functionality | SCRUM-01 :sparkles: feat(auth): add login endpoint |
| :bug: fix | Bug fix | SCRUM-01 :bug: fix(etl): fix duplicate record handling |
| :wrench: chore | Maintenance, no direct impact | SCRUM-01 :wrench: chore(deps): update project dependencies |
| :books: docs | Documentation changes | SCRUM-01 :books: docs(readme): update setup instructions |
| :art: style | Formatting only, no behavior change | SCRUM-01 :art: style(css): fix indentation |
| :recycle: refactor | Code refactoring | SCRUM-01 :recycle: refactor(pipeline): remove redundant checks |
| :zap: perf | Performance improvements | SCRUM-01 :zap: perf(api): reduce search endpoint response time |
| :test_tube: test | Adding or adjusting tests | SCRUM-01 :test_tube: test(etl): add unit tests for cleaning step |
| :building_construction: build | Build or external dependency changes | SCRUM-01 :building_construction: build(docker): add Dockerfile |
| :robot: ci | CI/CD changes | SCRUM-01 :robot: ci(workflow): update GitHub Actions workflow |
| :rewind: revert | Revert a previous commit | SCRUM-01 :rewind: revert(auth): revert "feat(auth): add JWT login" |
| :ambulance: hotfix | Urgent production fix | SCRUM-01 :ambulance: hotfix(etl): fix broken DataJud client |

</details>

<br>

<h1 id="gear-sonarqube">📚 SonarQube Monitoring</h1>

<div align="center">
  <p>SonarQube is used to automatically analyze the codebase, catch issues early, and keep the project clean, secure and standardized — reducing rework and easing maintenance.</p>
</div>

<h1 id="gear-documentation">📚 Documentation</h1>

<div align="center">
  <p>Full technical documentation (data model, dictionary, API reference, deployment guide) will be published in the project's documentation repository as it becomes available.</p>
</div>

| Document | Description |
|---|---|
| [Handover Guide](docs/handover/README.md) | Starting point for the client team, with checklist and risk register |
| [Requirements](docs/requirements/README.md) | Requirements specification, use cases and traceability matrix |
| [Code Governance](docs/governance/code-governance.md) | Branching, commits, reviews and quality gates |
| [Infrastructure](docs/infrastructure/infrastructure.md) | Environments, CI/CD, secrets and operations runbook |
| [Code Guide](docs/code/code-guide.md) | Code structure, business rules, endpoints and extension guides |
| [Test Cases](docs/testing/test-cases.md) | Test strategy, coverage and catalogue of the automated test cases (backend and frontend) |

<br>

<p align="center">
© 2026 — DataTech / DataLaw Project</p>
<p align="center">
Developed in the educational context of Fatec São Paulo, in partnership with Xertica.
</p>
