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
DATABASE_URL=postgresql+psycopg://datalaw:datalaw@localhost:5432/datalaw_db
```

### Database migrations

With PostgreSQL running and `DATABASE_URL` configured, create the database
structure defined by the SQLAlchemy models:

```bash
uv run alembic upgrade head
```

Whenever a model changes, generate and review a migration before applying it:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
```

### Run the Ingestion

Run the historical load once before the incremental routine:

```bash
uv run task full-ingest
```

It downloads every TJSP candidate with a definitive discharge or archival movement in the last six months, then persists only records whose same movement `22` or `246` occurred in that period.

After a successful historical load, run the daily incremental update manually:

```bash
uv run python -m data_law.main
```

The incremental routine rechecks the prior 48 hours of DataJud updates, adds newly finalized processes, and refreshes new movements for processes already held in Bronze.

Raw API responses are automatically saved as compressed, immutable pages under:

```text
data/raw/tjsp/ingestion_date=YYYY-MM-DD/run_id=.../page-000001.json.gz
```

### Reprocess Raw Files

To process files already saved in `data/raw`, run:

```bash
uv run task bronze-load
```
### Code Quality

```bash
uv run ruff format src tests
uv run ruff check src tests
```
<h1 id="white_check_mark-requirements">✅ Requirements</h1>

<details>
  <summary>Functional Requirements (RF)</summary>

| ID | Title | Description |
|---|---|---|
| RF01 | Simplified Query	| Allow natural language questions that return direct indicators |
| RF02 | Single-screen Metrics | Display adherence, processing time, and case volume in one unified interface |
| RF03 | Basic Filters | Enable filtering by court, topic, and period without complex navigation |
| RF04 | Semantic Search | Support meaning-based search to find related precedents |
| RF05 | DataJud extraction | Extract decisions from the DataJud (CNJ) API |
| RF06 | Open data extraction | Extract data from open government data portals |
| RF07 | Data cleaning | Clean and standardize data extracted from heterogeneous sources |
| RF08 | Dimensional storage | Store data in a dimensional model (Fact: Decision/Case; Dimensions: Court, Topic, Author, Document Type, Period) |
| RF09 | Semantic indexing | Semantically index documents to enable meaning-based search |
| RF10 | Semantic search | Support search by meaning/context, not only by keyword |
| RF11 | OLAP queries | Support multidimensional queries by court, topic and period |
| RF12 | Indicator dashboards | Display dashboards with adherence, processing time and volume indicators |
| RF13 | Source & reliability | Display the original source and a reliability indicator with every result |
| RF14 | Outcome classification | Classify the outcome of each decision (favorable/unfavorable, adherent/non-adherent to precedent) via NLP |

</details>

<details>
  <summary>Non-Functional Requirements (RNF)</summary>

| ID | Title | Description |
|---|---|---|
| RNF01 | Data model documentation | Conceptual, logical and physical dimensional model, plus a data dictionary |
| RNF02 | API documentation | All API endpoints must be documented |
| RNF03 | Language | Built in Python |
| RNF04 | Framework | Built with Django |
| RNF05 | Unit/integration tests | Automated unit and/or integration tests to ensure data integrity |
| RNF06 | Functional tests | Automated functional tests at API and UI level |
| RNF07 | Static analysis | Continuous static code analysis |
| RNF08 | DevOps / CI-CD | CI/CD pipeline with technically justified tooling |
| RNF09 | Scope restriction | Data scope restricted to civil law across all covered courts (STF, STJ, TJ) |
| RNF10 | Traceability | Full traceability between requirement, backlog and delivery, managed via Jira |
| RNF11 | Version control | Source code versioned in Git |

</details>

<br>

<h1 id="card_file_box-product-backlog">🗂 Product Backlog</h1>

| Rank | Priority | User Story | Points | Sprint | DOR |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Critical | As a Strategic Lawyer, I want to filter decisions by court and period, so that I can quickly locate relevant jurisprudence for my case. | 8 | 1 | Court and period fields defined, dataset available, filtering rules documented |
| 1.4 | High | As the system, I need to display the original source and a reliability indicator for each result, so that transparency is ensured for the user. | 3 | 1 | Reliability rules documented, metadata available |
| 1.2 | High | As a Strategic Lawyer, I want to consult decisions from STJ, STF, and State Courts already cleaned and standardized, so that I reduce the time spent gathering jurisprudence from different sources. | 5 | 1 | Raw decisions collected, cleaning rules defined |
| 1.3 | High | As a Lawyer/Judge, I want to search and visualize real decisions in a simple way, so that I can validate that the system already provides useful data from the start. | 5 | 1 | Search endpoints defined, sample dataset ready |
| 1.5 | Medium | As a Legal Manager, I want the data structure and API of the platform to be well documented and traceable from the beginning, so that I can trust the numbers used in financial decisions. | 3 | 1 | Data model finalized, API endpoints listed, documentation template ready |
| 2.3 | Critical | As a Strategic Lawyer, I want each decision’s legal topic to be automatically classified and searchable by meaning, so that I don’t depend on exact keywords. | 8 | 2 | NLP model selected, classification rules defined |
| 2.4 | Critical | As a Lawyer/Judge, I want to search by meaning and perform multidimensional queries (by court, topic, period), so that I can find related precedents and identify jurisprudence patterns. | 8 | 2 | Semantic index available, query parameters defined, test cases prepared |
| 2.5 | High | As a Strategic Lawyer, I want the presented data to always be correct, consistent, and technically reliable, so that I can trust the information when building an argument. | 5 | 2 | Data validation rules defined, quality checks automated |
| 2.1 | High | As a Legal Manager, I want open data portal information to enrich the context of decisions, so that I have a more complete view when analyzing a case. | 8 | 2 | Open data sources identified, access validated, enrichment rules defined |
| 2.2 | Medium | As a Legal Manager, I want to filter decisions also by topic, author, and document type, so that I can perform more complete analyses of a case or thesis. | 5 | 2 | Dimensions identified, schema updated, filtering logic documented |
| 3.3 | Critical | As a Judge, I want to visualize dashboards with doctrinal trends, so that I can support strategic decisions. | 8 | 3 | Dashboard requirements defined, OLAP model ready, visualization tool selected |
| 3.4 | Critical | As a Judge, I want all platform functionalities to operate correctly and updates not to break existing features, so that usage is not impacted. | 8 | 3 | Regression test plan defined, CI/CD pipeline available, monitoring configured |
| 3.2 | High | As the system, I need to extract legal entities (parties, courts, cited legislation), so that structured data is enriched. | 8 | 3 | NLP entity extraction model defined, training dataset ready, validation rules set |
| 3.1 | Medium | As the system, I need to collect content from doctrine repositories, so that doctrine is included as a source of analysis. | 8 | 3 | Doctrine sources identified, access validated |

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

[x] Business rules defined: which court and decision types to extract.

[x] Data available: API access key configured and validated.

[x] Prototype approved: initial data ingestion flow documented.

</details>

<details>
<summary><strong>US1.2 — Clean and standardize the extracted decisions</strong></summary>

DoR Checklist

[x] Business rules defined: cleaning rules documented (remove duplicates, normalize fields).

[x] Data available: raw dataset ready for cleaning.

[x] Prototype approved: schema for cleaned dataset validated.


</details>

<details>
<summary><strong>US1.3 — Build a minimal dimensional model (Fact + Court, Topic, Period, Outcome)</strong></summary>

DoR Checklist

[x] Business rules defined: fact table and dimensions documented.

[x] Data available: cleaned dataset mapped to dimensional schema.

[x] Prototype approved: ER diagram or schema mockup available.

</details>

<details>
<summary><strong>US1.4 — Calculate the adherence rate for one pilot legal topic</strong></summary>

DoR Checklist

[x] Business rules defined: adherence calculation formula agreed with stakeholders.

[x] Data available: pilot dataset with topic classification.

[x] Prototype approved: metric displayed in single-screen interface.

</details>

<details>
<summary><strong>US1.5 — Display source and reliability indicator next to the pilot metric</strong></summary>

DoR Checklist

[x] Business rules defined: reliability calculation method documented.

[x] Data available: metadata accessible for each decision.

[x] Prototype approved: source and reliability displayed next to metrics.

</details>

<details>
<summary><strong>US1.6 — Build a simple query interface to view supporting decisions</strong></summary>

DoR Checklist

[x] Business rules defined: query parameters documented (court, topic, period).

[x] Data available: pilot dataset indexed for queries.

[x] Messages defined: error if query returns no results; success confirmation when decisions are displayed.

[x] Prototype approved: query interface mockup validated.

</details>

<details>
<summary><strong>US1.7 — Document the initial data model and dictionary</strong></summary>

DoR Checklist

[x] Business rules defined: documentation template agreed.

[x] Data available: dimensional schema finalized.

[x] Messages defined: documentation must include validation notes.

[x] Prototype approved: draft data dictionary reviewed.

</details>

<details>
<summary><strong>US1.8 — Set up Jira project and traceability structure</strong></summary>

DoR Checklist

[x] Business rules defined: backlog structure mapped to requirements.

[x] Data available: Jira project created with access for all team members.

[x] Messages defined: notifications configured for backlog changes.

[x] Prototype approved: Jira board structure validated.

</details>

</details>

<details>
  <summary><b>Sprint 2</b></summary>

### **Sprint 2: Planning and Execution**

* **Sprint Goal:** Expand data coverage to the full defined scope (all TJs, open data portals), turn on NLP-based intelligence (topic classification, entity extraction, semantic indexing) and enable semantic search and the average processing time indicator.
* **Estimated Capacity:** 60 story points

| Rank | Priority | User Story | Points |
| --- | --- | --- | --- |
| 2.4 | Critical | Classify legal topic automatically via NLP | 8 |
| 2.6 | Critical | Semantically index all documents | 8 |
| 2.7 | Critical | Support natural language semantic search | 5 |
| 2.8 | Critical | Calculate average case processing time by court/topic | 8 |
| 2.5 | High | Extract legal entities via NLP | 8 |
| 2.1 | High | Extract decisions from remaining State Court (TJ) APIs | 8 |
| 2.3 | High | Expand dimensional model with remaining dimensions | 5 |
| 2.9 | High | Add automated unit and integration tests for ETL and dimensional model | 5 |
| 2.2 | Medium | Extract data from open government data portals | 5 |

<details>
<summary><strong>US2.4 — Classify legal topic automatically via NLP</strong></summary>

DoR Checklist

[x] Business rules defined: topic classification logic documented.

[x] Data available: training dataset prepared and validated.

[x] Prototype approved: topic field visible in search results.

</details>

<details>
<summary><strong>US2.6 — Semantically index all documents</strong></summary>

DoR Checklist

[x] Business rules defined: semantic indexing parameters documented.

[x] Data available: dataset indexed with semantic model.

[x] Prototype approved: semantic index validated with sample queries.

</details>

<details>
<summary><strong>US2.7 — Support natural language semantic search</strong></summary>

DoR Checklist

[x] Business rules defined: query parameters documented for semantic search.

[x] Data available: indexed dataset validated for queries.

[x] Prototype approved: semantic search bar mockup validated.

</details>

<details>
<summary><strong>US2.8 — Calculate average case processing time by court/topic</strong></summary>

DoR Checklist

[x] Business rules defined: calculation formula documented.

[x] Data available: dataset with timestamps validated.

[x] Prototype approved: metric displayed in single-screen interface.

</details>

<details>
<summary><strong>US2.5 — Extract legal entities via NLP</strong></summary>

DoR Checklist

[x] Business rules defined: entity extraction rules documented (parties, courts, legislation).

[x] Data available: training dataset prepared and validated.

[x] Prototype approved: entities displayed in structured format.

</details>

<details>
<summary><strong>US2.1 — Extract decisions from remaining State Court (TJ) APIs</strong></summary>

DoR Checklist

[x] Business rules defined: which State Courts and decision types to extract.

[x] Data available: API endpoints validated and accessible.

[x] Prototype approved: ingestion flow documented for multiple courts.

</details>

<details>
<summary><strong>US2.3 — Expand dimensional model with remaining dimensions</strong></summary>

DoR Checklist

[x] Business rules defined: additional dimensions documented (author, document type).

[x] Data available: schema updated with new dimensions.

[x] Prototype approved: ER diagram updated with new dimensions.

</details>

<details>
<summary><strong>US2.9 — Add automated unit and integration tests for ETL and dimensional model</strong></summary>

DoR Checklist

[x] Business rules defined: test coverage requirements documented.

[x] Data available: sample datasets prepared for testing.

[x] Prototype approved: CI/CD pipeline configured to run tests.

</details>

<details>
<summary><strong>US2.2 — Extract data from open government data portals</strong></summary>

DoR Checklist

[x] Business rules defined: enrichment rules documented for open data sources.

[x] Data available: open data sources identified and validated.

[x] Prototype approved: schema updated to include enriched fields.

</details>

</details>

<details>
  <summary><b>Sprint 3</b></summary>

### **Sprint 3: Planning and Execution**

* **Sprint Goal:** Consolidate the platform — bring in doctrine as a data source, complete outcome classification, ship full OLAP dashboards, and close out the mandatory non-functional requirements (functional testing, CI/CD).
* **Estimated Capacity:** 37 story points

| Rank | Priority | User Story | Points |
| --- | --- | --- | --- |
| 3.3 | Critical | Ship complete OLAP-backed dashboards (adherence, processing time, volume) | 8 |
| 3.4 | Critical | Add automated functional tests (API and UI) | 8 |
| 3.2 | High | Classify decision outcome (favorable/unfavorable, adherent/non-adherent) | 8 |
| 3.1 | Medium | Collect content from legal doctrine repositories | 8 |
| 3.5 | Medium | Set up CI/CD pipeline | 5 |

<details>
<summary><strong>US3.3 — Ship complete OLAP-backed dashboards (adherence, processing time, volume)</strong></summary>

DoR Checklist

[x] Business rules defined: KPIs documented (adherence %, average time, case volume).

[x] Data available: OLAP model finalized and validated.

[x] Prototype approved: dashboard mockup with charts reviewed.

</details>

<details>
<summary><strong>US3.4 — Add automated functional tests (API and UI)</strong></summary>

DoR Checklist

[x] Business rules defined: functional test coverage requirements documented.

[x] Data available: test cases prepared for API and UI.

[x] Prototype approved: CI/CD pipeline configured to run functional tests.

</details>

<details>
<summary><strong>US3.2 — Classify decision outcome (favorable/unfavorable, adherent/non-adherent)</strong></summary>

DoR Checklist

[x] Business rules defined: classification logic documented (outcome categories).

[x] Data available: dataset labeled with outcomes for training.

[x] Prototype approved: outcome field visible in decision results.

</details>

<details>
<summary><strong>US3.1 — Collect content from legal doctrine repositories</strong></summary>

DoR Checklist

[x] Business rules defined: doctrine sources identified and validated.

[x] Data available: access confirmed to repositories.

[x] Prototype approved: schema updated to include doctrine content.

</details>

<details>
<summary><strong>US3.5 — Set up CI/CD pipeline</strong></summary>

DoR Checklist

[x] Business rules defined: CI/CD workflow documented (build, test, deploy).

[x] Data available: environment variables and secrets configured.

[x] Prototype approved: pipeline configuration validated in GitHub Actions/Docker.

</details>

</details>

<br>

<h1 id="hourglass_flowing_sand-project-timeline">⏳ Project Timeline</h1>

- [x] Kick-off with partner (Xertica)
- [x] Discovery follow-up: additional stakeholder questions to refine the real business pain point
- [x] Sprint 1 — Planning
- [x] Sprint 1 — Execution
- [ ] Sprint 1 — Review / Sprint 2 Planning
- [ ] Sprint 2 — Execution
- [ ] Sprint 2 — Review / Sprint 3 Planning
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

**Pull Requests:** opened after a task is complete, referencing all involved Task IDs, with a detailed description of what was implemented. Each task should have its own Pull Request.

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

<br>

<p align="center">
© 2026 — DataTech / DataLaw Project</p>
<p align="center">
Developed in the educational context of Fatec São Paulo, in partnership with Xertica.
</p>
