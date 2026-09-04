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

The application allows users to:
- Ask **business questions in natural language** and receive a direct, indicator-based answer;
- Track **adherence rate** of a court to a given topic or precedent;
- Monitor **average case processing time** by court and topic;
- Explore **multidimensional (OLAP) analysis** by court, topic, document type and period;
- Perform **semantic search**, finding related precedents even when different terminology is used;
- Always see the **original source and a reliability indicator** next to every result.

**Target users:**
- **Legal Managers / Legal Ops / Executives** — evaluate success rates of legal theses and average processing time to support financial decisions (risk provisioning, settle vs. litigate).
- **Strategic Lawyers** — identify the prevailing position of courts on emerging legal theses and estimate the probability of success before filing an action or appeal.
- **Judges / Judicial Analysts** — track volume and adherence to binding precedents (STF/STJ) to manage stalled or pending case backlogs.

**Scope:** STF (constitutional matters), STJ (unifying precedents) and TJ (state-level case law) — restricted exclusively to **civil law** across all three instances.

<br>

<h1 id="white_check_mark-requirements">✅ Requirements</h1>

<details>
  <summary>Functional Requirements (RF)</summary>

| ID | Title | Description |
|---|---|---|
| RF01 | DataJud extraction | Extract decisions from the DataJud (CNJ) API |
| RF02 | State Court extraction | Extract decisions from State Court of Justice (TJ) APIs |
| RF03 | Open data extraction | Extract data from open government data portals |
| RF04 | Doctrine collection | Collect content from legal doctrine repositories |
| RF05 | Data cleaning | Clean and standardize data extracted from heterogeneous sources |
| RF06 | Dimensional storage | Store data in a dimensional model (Fact: Decision/Case; Dimensions: Court, Topic, Author, Document Type, Period) |
| RF07 | Topic classification | Automatically classify the legal topic of each decision via NLP |
| RF08 | Entity extraction | Extract legal entities and concepts via NLP |
| RF09 | Semantic indexing | Semantically index documents to enable meaning-based search |
| RF10 | Semantic search | Support search by meaning/context, not only by keyword |
| RF11 | OLAP queries | Support multidimensional queries by court, topic and period |
| RF12 | Indicator dashboards | Display dashboards with adherence, processing time and volume indicators |
| RF13 | Source & reliability | Display the original source and a reliability indicator with every result |
| RF14 | Query interface | Provide an interface where users ask business questions and view supporting decisions |
| RF15 | Adherence rate | Calculate a court's adherence rate to a given topic or precedent |
| RF16 | Average processing time | Calculate average case processing time by court and topic |
| RF17 | Outcome classification | Classify the outcome of each decision (favorable/unfavorable, adherent/non-adherent to precedent) via NLP |
| RF18 | Natural language answers | Answer natural language questions about indicators (e.g. "which court has the highest adherence to Topic X?") |

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

| Rank | Priority | User Story | Points | Sprint |
|---|---|---|---|---|
| 1.1 | Highest | As the system, I want to extract decisions from the DataJud (CNJ) API for a pilot court, so that a real, usable dataset is available to build the first indicator. | 8 | 1 |
| 1.2 | Highest | As the system, I want to clean and standardize the extracted decisions, so that inconsistent formats don't break downstream calculations. | 5 | 1 |
| 1.3 | Highest | As a data team, I want a minimal dimensional model (Fact: Decision; Dimensions: Court, Topic, Period, Outcome), so that the first indicator can be stored and queried. | 5 | 1 |
| 1.4 | Highest | As a Legal Ops manager, I want to see the adherence rate of a court to one pilot legal topic, so that I can validate the platform against a metric I already care about. | 8 | 1 |
| 1.5 | High | As any user, I want to see the original source and a reliability indicator next to the pilot metric, so that I can trust the number before using it in a decision. | 3 | 1 |
| 1.6 | High | As any user, I want a simple query interface to view the decisions behind the pilot indicator, so that I can audit how the number was calculated. | 3 | 1 |
| 1.7 | Medium | As a team, we want the initial data model and dictionary documented, so that the project remains traceable from day one. | 3 | 1 |
| 1.8 | Medium | As a team, we want the Jira project and traceability structure set up, so that every requirement maps to a backlog item. | 1 | 1 |
| 2.1 | High | As the system, I want to extract decisions from State Court (TJ) APIs beyond the pilot court, so that coverage expands to the full defined scope. | 8 | 2 |
| 2.2 | Medium | As the system, I want to extract data from open government data portals, so that processual context is enriched. | 5 | 2 |
| 2.3 | High | As a data team, I want to expand the dimensional model with all remaining dimensions (Author, Document Type), so that OLAP analysis is fully supported. | 5 | 2 |
| 2.4 | Highest | As the system, I want to automatically classify the legal topic of each decision via NLP, so that documents are organized without manual tagging. | 8 | 2 |
| 2.5 | High | As the system, I want to extract legal entities from each decision via NLP, so that the outcome classification indicator has richer input. | 8 | 2 |
| 2.6 | Highest | As the system, I want to semantically index all documents, so that search can operate by meaning rather than keyword. | 8 | 2 |
| 2.7 | Highest | As a strategic lawyer, I want to search using natural language questions, so that I can find related precedents even with different terminology. | 5 | 2 |
| 2.8 | Highest | As the system, I want to calculate the average case processing time by court and topic, so that Legal Ops can support settlement vs. litigation decisions. | 8 | 2 |
| 2.9 | High | As a team, we want automated unit and integration tests covering the ETL and dimensional model, so that data integrity is protected as scope grows. | 5 | 2 |
| 3.1 | Medium | As the system, I want to collect content from legal doctrine repositories, so that doctrinal analysis becomes possible. | 8 | 3 |
| 3.2 | High | As the system, I want to classify the outcome of each decision (favorable/unfavorable, adherent/non-adherent), so that success-rate indicators are accurate. | 8 | 3 |
| 3.3 | Highest | As a judge or Legal Ops manager, I want complete OLAP-backed dashboards for adherence, processing time and volume, so that I can support strategic and financial decisions. | 8 | 3 |
| 3.4 | Highest | As a team, we want automated functional tests at API and UI level, so that the full system is validated end to end. | 8 | 3 |
| 3.5 | Medium | As a team, we want a CI/CD pipeline in place, so that tests and deployment are automated on every change. | 5 | 3 |

<br>

<h1 id="calendar-sprint-backlog">📅 Sprint Backlog</h1>

<details>
  <summary><b>Sprint 1</b></summary>

### **Sprint 1: Planning and Execution**

* **Sprint Goal:** Prove the core value proposition end to end — extract real decisions for one pilot court and topic, calculate one trustworthy business indicator (adherence rate), and display it with full source traceability. This validates the actual pain point identified with the client, rather than delivering a generic search screen.
* **Estimated Capacity:** 36 story points
* **Blocking dependency:** the business rule for what counts as "adherence"/"success" must be confirmed with the client before Story 1.4 can be reliably estimated and started.

| Rank | Priority | User Story | Points |
|---|---|---|---|
| 1.1 | Highest | Extract decisions from the DataJud (CNJ) API for a pilot court | 8 |
| 1.2 | Highest | Clean and standardize the extracted decisions | 5 |
| 1.3 | Highest | Build a minimal dimensional model (Fact + Court, Topic, Period, Outcome) | 5 |
| 1.4 | Highest | Calculate the adherence rate for one pilot legal topic | 8 |
| 1.5 | High | Display source and reliability indicator next to the pilot metric | 3 |
| 1.6 | High | Build a simple query interface to view supporting decisions | 3 |
| 1.7 | Medium | Document the initial data model and dictionary | 3 |
| 1.8 | Medium | Set up Jira project and traceability structure | 1 |

### **Definition of Ready (DoR)**

A backlog item is ready for the sprint if it meets the following:

* Clear title, description and objective.
* Acceptance criteria and business rules defined (e.g. what counts as "adherence" or "success").
* Priority established.
* Effort estimated by the team.
* Data source/access confirmed as available, or a fallback plan exists.
* Dependencies on other stories mapped and flagged in Jira.
* Traceable to the originating RF/RNF.

### **Definition of Done (DoD)**

A backlog item is considered done if:

* Code has been written, tested locally and follows the team's code standards.
* Reviewed and approved by peers.
* Merged into the main integration branch.
* Automated tests created and passing.
* Acceptance criteria met.
* The computed indicator has been validated against the client's own reference numbers.
* The Product Owner has approved the functionality.

</details>

<details>
  <summary><b>Sprint 2</b></summary>

### **Sprint 2: Planning and Execution**

* **Sprint Goal:** Expand data coverage to the full defined scope (all TJs, open data portals), turn on NLP-based intelligence (topic classification, entity extraction, semantic indexing) and enable semantic search and the average processing time indicator.
* **Estimated Capacity:** 60 story points

| Rank | Priority | User Story | Points |
|---|---|---|---|
| 2.1 | High | Extract decisions from remaining State Court (TJ) APIs | 8 |
| 2.2 | Medium | Extract data from open government data portals | 5 |
| 2.3 | High | Expand dimensional model with remaining dimensions | 5 |
| 2.4 | Highest | Classify legal topic automatically via NLP | 8 |
| 2.5 | High | Extract legal entities via NLP | 8 |
| 2.6 | Highest | Semantically index all documents | 8 |
| 2.7 | Highest | Support natural language semantic search | 5 |
| 2.8 | Highest | Calculate average case processing time by court/topic | 8 |
| 2.9 | High | Add automated unit and integration tests for ETL and dimensional model | 5 |

### **Definition of Ready (DoR)**

* Same criteria as Sprint 1.
* NLP tool has been technically evaluated (e.g. Pangea, cited as a market reference by the client) and a decision made or explicitly deferred.
* Sample input/output for the NLP pipeline reviewed with the Product Owner.

### **Definition of Done (DoD)**

* Same criteria as Sprint 1.
* No new issues introduced in SonarQube.
* Technical documentation updated by developers.
* Semantic search results manually validated against a sample of real queries.

</details>

<details>
  <summary><b>Sprint 3</b></summary>

### **Sprint 3: Planning and Execution**

* **Sprint Goal:** Consolidate the platform — bring in doctrine as a data source, complete outcome classification, ship full OLAP dashboards, and close out the mandatory non-functional requirements (functional testing, CI/CD).
* **Estimated Capacity:** 37 story points

| Rank | Priority | User Story | Points |
|---|---|---|---|
| 3.1 | Medium | Collect content from legal doctrine repositories | 8 |
| 3.2 | High | Classify decision outcome (favorable/unfavorable, adherent/non-adherent) | 8 |
| 3.3 | Highest | Ship complete OLAP-backed dashboards (adherence, processing time, volume) | 8 |
| 3.4 | Highest | Add automated functional tests (API and UI) | 8 |
| 3.5 | Medium | Set up CI/CD pipeline | 5 |

### **Definition of Ready (DoR)**

* Same criteria as previous sprints.
* Dashboard KPIs and visualizations reviewed and approved with the Product Owner.

### **Definition of Done (DoD)**

* Same criteria as previous sprints.
* Full regression suite (unit, integration, functional) passing in CI/CD.
* Final data model, dictionary and API documentation published.
* Application is responsive and follows the team's design/style guide.

</details>

<br>

<h1 id="hourglass_flowing_sand-project-timeline">⏳ Project Timeline</h1>

- [x] Kick-off with partner (Xertica)
- [x] Discovery follow-up: additional stakeholder questions to refine the real business pain point
- [ ] Sprint 1 — Planning
- [ ] Sprint 1 — Execution
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
- **Python + Django** — suggested by the partner (Xertica); mature ORM, well suited for exposing APIs on top of the dimensional model.
- **PostgreSQL** — open-source, handles analytical workloads well and supports search-related extensions.
- **NLP** — Pangea was cited by the partner as a strong market reference during kick-off; it is the first option to be technically evaluated for topic classification and entity extraction. Final tool selection is pending validation.
- **SonarQube** — continuous static code analysis, an explicit requirement from Fatec.
- **Docker + GitHub Actions** — consistent environments and automated CI/CD.
- **Jira** — maps natively to the team's workflow (Problem → Solution Proposal → Requirements → MVP → Product Backlog → DoR → Sprint Backlog → Version Control), giving full traceability from requirement to delivery.
- **VS Code** — standardizes the development environment across the team.

<br>

<h1 id="gear-branching-strategy">🌿 Branching Strategy and Commit Pattern</h1>

<details>
  <summary><b>Branching Strategy</b></summary>

**Typical workflow:**
1. Create a **feature branch** from `develop`.
2. Develop the functionality.
3. Rebase/update the branch against `develop` to avoid conflicts.
4. Open a **Pull Request** to `develop`.
5. After the required approvals, merge into `develop`.

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
| feat | New functionality | SCRUM-01 feat(auth): add login endpoint |
| fix | Bug fix | SCRUM-01 fix(etl): fix duplicate record handling |
| chore | Maintenance, no direct impact | SCRUM-01 chore(deps): update project dependencies |
| docs | Documentation changes | SCRUM-01 docs(readme): update setup instructions |
| style | Formatting only, no behavior change | SCRUM-01 style(css): fix indentation |
| refactor | Code refactoring | SCRUM-01 refactor(pipeline): remove redundant checks |
| perf | Performance improvements | SCRUM-01 perf(api): reduce search endpoint response time |
| test | Adding or adjusting tests | SCRUM-01 test(etl): add unit tests for cleaning step |
| build | Build or external dependency changes | SCRUM-01 build(docker): add Dockerfile |
| ci | CI/CD changes | SCRUM-01 ci(workflow): update GitHub Actions workflow |
| revert | Revert a previous commit | SCRUM-01 revert(auth): revert "feat(auth): add JWT login" |
| hotfix | Urgent production fix | SCRUM-01 hotfix(etl): fix broken DataJud client |

**Branch naming:**
```
git checkout -b SCRUM-1/create-login-screen
```

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
