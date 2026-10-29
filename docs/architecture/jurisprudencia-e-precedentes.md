# Architecture and Collection Strategy for Case Law and Binding Precedents — DataLaw

This document defines the origin, collection, classification, and publication of case law and binding precedents within DataLaw. It specifies how those materials are correlated with subjects in the Unified Procedural Table (Tabela Processual Unificada, TPU) and how they are made available in the application, in accordance with the Brazilian General Data Protection Law (Lei Geral de Proteção de Dados, LGPD) and the principles of the Medallion Architecture.

---

## 1. Conditions for the Publication of Case Law

DataLaw applies two governance rules before case law or binding precedents are published for a procedural subject.

1. **Statistical significance ($N \ge 30$).** A subject enters the Gold analytical layer only when at least 30 valid proceedings for that subject have been recorded in the court.
2. **Qualified linkage by TPU code.** Publication further requires a direct correspondence between the TPU code of the procedural subject (`silver.processo_assunto.codigo`) and the classification of the registered precedent (`silver.jurisprudencia.assunto_codigo`).

Certain subjects satisfy the threshold $N \ge 30$ and remain pending the load of binding precedents for their respective codes. These include *Multas e demais Sanções* (TPU `10023`), *Pena de Multa* (TPU `7792`), and *ICMS* (TPU `5946`). Precedents for those codes are introduced through continuous ingestion batches into the catalogue.

---

## 2. Official Sources of Case Law

Case law and precedents are extracted in batch from official public sources and served from locally materialized records. User navigation does not trigger synchronous queries against external court systems.

### A. National Bank of Precedents (BNPR / CNJ)

- **Description.** Repository maintained by the National Council of Justice (Conselho Nacional de Justiça, CNJ), consolidating qualified precedents from courts throughout Brazil.
- **Records obtained.** Statements of binding summaries (*súmulas*), Repetitive Appeal Themes of the Superior Court of Justice (Superior Tribunal de Justiça, STJ), and General Repercussion Themes of the Federal Supreme Court (Supremo Tribunal Federal, STF).
- **Access.** CNJ open-data catalogues and application programming interface.
- **Integration keys.** TPU subject code and TPU movement or precedent code.

### B. Superior Court of Justice (STJ — Case Law and Repetitive Themes)

- **Description.** Official repository of theses and of *Jurisprudência em Teses* published by the STJ.
- **Records obtained.** Theme number, established thesis, leading judgment (*acórdão paradigma*), and the reporting justice's headnote (*ementa*).
- **Illustrative correlation.** TPU subject `5952` (IPTU) corresponds to Repetitive Theme 1043 and to STJ *Súmula* 397.

### C. Federal Supreme Court (STF — General Repercussion)

- **Description.** Repository of binding theses and of themes in which general repercussion has been recognized.
- **Records obtained.** General-repercussion thesis and the headnote of the judgment on the merits.
- **Illustrative correlation.** TPU subject `5961` (municipal fees) corresponds to STF Theme 217.

### D. Court of Justice of the State of São Paulo (TJSP — Binding Summaries and Statements)

- **Description.** TJSP case-law consultation portal and the statements of its specialized chambers (Public Law and Private Law).
- **Records obtained.** Statements of the Public Law Chambers, TJSP *súmulas*, and headnotes of Repetitive Claims Resolution Incidents (Incidentes de Resolução de Demandas Repetitivas, IRDR).

---

## 3. Processing within the Medallion Pipeline

```text
[BNPR / STJ / STF / TJSP]
           │
           │ 1. Batch ingestion (Python)
           ▼
┌────────────────────────────────────────┐
│ bronze.jurisprudencia_extract           │  Raw JSON payload from the API or open data
└────────────────────────────────────────┘
           │
           │ 2. Normalization and LGPD minimization
           ▼
┌────────────────────────────────────────┐
│ silver.jurisprudencia                  │  Thesis, headnote, court, reporting justice, assunto_codigo
└────────────────────────────────────────┘
           │
           │ 3. Aggregation under the rule N >= 30
           ▼
┌────────────────────────────────────────┐
│ gold.topic_precedents                  │  Join with silver.processo_assunto (N >= 30)
└────────────────────────────────────────┘
           │
           │ 4. Local consumption (Spring Boot JPA)
           ▼
[DataLaw dashboard — localhost:8080]
```

### Data minimization (LGPD)

The pipeline retains exclusively the public elements of the judicial thesis: the precedent number, a summarized headnote, the established thesis, the collegiate body, and the reporting justice.

The following categories are excluded from ingestion: names of private parties, personal identification documents (CPF and RG), residential addresses, and proceedings under judicial secrecy (`nivelSigilo > 0`).

---

## 4. Query Mechanism in the Application (Java / Spring Boot)

When the user selects a bar in the subject chart on the dashboard, the application proceeds as follows.

1. The client issues an asynchronous internal request:

   ```http
   GET /processos/taxa-sucesso-tema?assuntoNome=IPTU/%20Imposto%20Predial%20e%20Territorial%20Urbano
   ```

2. [`ProcessoController`](frontend/src/main/java/com/datatech/datalaw/controller/ProcessoController.java) invokes [`ProcessoRepository.findPrecedentesPorAssunto()`](frontend/src/main/java/com/datatech/datalaw/repository/ProcessoRepository.java):

   ```sql
   SELECT tribunal_precedente, identificador_precedente, precedente_titulo, precedente_tese, precedente_ementa
   FROM gold.topic_precedents
   WHERE assunto_nome = :assuntoNome
   ORDER BY identificador_precedente;
   ```

3. The JSON response is rendered within the interface modal, presenting the success indicator together with the applicable binding precedents.

---

## 5. Registration of Precedents for Additional Subjects

Additional subjects, such as *Multas e demais Sanções* (TPU `10023`) and *ICMS* (TPU `5946`), are incorporated by registering each precedent against its TPU code and rematerializing the downstream layers. Illustrative payload values below remain in Portuguese, as they reproduce the wording stored from the source systems.

1. Register the precedent, including its TPU code, in the ingestion script [`backend/src/data_law/ingestion/jurisprudencia.py`](backend/src/data_law/ingestion/jurisprudencia.py):

   ```python
   {
       "fonte": "STJ",
       "tribunal_sigla": "STJ",
       "identificador_precedente": "Tema 456",
       "titulo": "Limites de juros e multas administrativas",
       "ementa": "A cobrança de penalidades administrativas...",
       "tese": "As multas e sanções administrativas sujeitam-se aos princípios da proporcionalidade e não-confisco.",
       "relator": "Min. Relator",
       "data_julgamento": date(2023, 8, 20),
       "assunto_codigo": 10023,
       "assunto_nome": "Multas e demais Sanções",
   }
   ```

2. Synchronize the Silver layer:

   ```bash
   python -m data_law.ingestion.jurisprudencia
   ```

3. Rematerialize the Gold layer:

   ```bash
   python -m data_law.transformation.gold --name topic_precedents
   ```

4. Upon completion of the rematerialization, the application displays the newly registered precedent. No restart of the service and no modification of the Java code are required.
