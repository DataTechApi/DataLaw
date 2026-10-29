<div align="center">

# TEST CASES
### DataLaw — Automated Test Documentation
#### Sprint 2

</div>

<p align="center">
  <a href="#memo-overview">Overview</a> •
  <a href="#arrow_forward-how-to-run">How to Run</a> •
  <a href="#dart-test-strategy">Test Strategy</a> •
  <a href="#bar_chart-coverage-summary">Coverage</a> •
  <a href="#test_tube-backend-test-cases">Backend Test Cases</a> •
  <a href="#test_tube-frontend-test-cases">Frontend Test Cases</a> •
  <a href="#warning-known-gaps">Known Gaps</a> •
  <a href="#robot-continuous-integration">CI</a>
</p>

<br>

<h1 id="memo-overview">📝 Overview</h1>

<p align="justify">
This document describes the automated test strategy of DataLaw and lists every test case currently implemented. Each test case shows the scenario being exercised and the expected result, so it can be reviewed without reading the test code. It supports the requirements <b>RNF05 — Unit/integration tests</b> and <b>RNF06 — Functional tests</b>, and the backlog items <b>SCRUM-131</b>, <b>SCRUM-133</b> and <b>SCRUM-134</b>.
</p>

| Area | Framework | Test cases | Executions | Result |
|---|---|---|---|---|
| Backend (`backend/tests`) | pytest | 143 | 252 (parametrized) | 251 passed, 1 skipped |
| Frontend (`frontend/src/test`) | JUnit 5, Mockito, Spring MockMvc | 14 | 14 | 14 passed |
| **Total** | | **157** | **266** | **265 passed, 1 skipped** |

<p align="justify">
The skipped test is the PostgreSQL integration test <code>test_postgres_merge_updates_only_changed_process</code>. It only runs when the <code>DATABASE_URL</code> environment variable is set.
</p>

## **Test Levels**

| Level | Status | Description |
|---|---|---|
| Unit | Implemented | Functions, services and controllers tested in isolation with fakes and mocks. No database, network or Docker required. |
| Integration | Planned | Real PostgreSQL (Testcontainers) for migrations, SQL Gold recipes and `ProcessoRepository` native queries. |
| End-to-end | Planned | Raw files → Bronze → Silver → Gold → dashboard. |

<br>

<h1 id="arrow_forward-how-to-run">▶️ How to Run</h1>

## **Backend**

```bash
cd backend
uv run task test
```

With the coverage report (installs `pytest-cov` only for this execution):

```bash
uv run --with pytest-cov pytest --cov=data_law --cov-branch --cov-report=term-missing
```

## **Frontend**

```bash
cd frontend
./mvnw test
```

With the JaCoCo coverage report (the plugin is called from the command line, so `pom.xml` does not need to change):

```bash
./mvnw org.jacoco:jacoco-maven-plugin:0.8.14:prepare-agent test org.jacoco:jacoco-maven-plugin:0.8.14:report
```

The report is generated at `frontend/target/site/jacoco/index.html`. On Windows PowerShell use `.\mvnw.cmd` instead of `./mvnw`.

> **Warning:** never export the `DATABASE_URL` from the project `.env` before running the tests. It points to the production database, and the integration test writes and deletes rows in `bronze.datajud_extract`.

<br>

<h1 id="dart-test-strategy">🎯 Test Strategy</h1>

- **Isolation:** external dependencies are replaced by test doubles — in-memory fake sessions and engines for PostgreSQL, `monkeypatch`/`unittest.mock` for the DataJud and BNP HTTP APIs, `tmp_path` for raw files, and `@MockitoBean` / `@Mock` for Spring beans.
- **Determinism:** dates are fixed or computed relative to `now`, and no test depends on execution order or on data stored in a real database.
- **Parametrization:** a single test case may run several times with different inputs (`@pytest.mark.parametrize`). The number of inputs is shown in the **Inputs** column.
- **Naming:** test names describe the behavior being verified (`test_<unit>_<expected_behavior>` in Python, descriptive method names in Java).
- **Markers:** tests that need PostgreSQL are marked with `@pytest.mark.integration` and skip automatically when no database is configured.

<details>
  <summary><b>Test Case ID Convention</b></summary>

Every test case is identified as `TC-<AREA>-<NUMBER>`.

| Prefix | Area |
|---|---|
| `TC-INF` | Database infrastructure (ORM mappings, sessions) |
| `TC-SMK` | Test suite smoke check |
| `TC-BRZ` | Bronze layer (raw files and upsert) |
| `TC-ING` | DataJud ingestion service and helpers |
| `TC-API` | DataJud HTTP client |
| `TC-STO` | Raw file storage |
| `TC-JUR` | Jurisprudence and precedents (BNP API) |
| `TC-CLI` | Command-line entry point |
| `TC-SLV` | Silver layer transformations |
| `TC-SYN` | Bronze → Silver synchronization |
| `TC-GLD` | Gold recipe registry and recipes |
| `TC-GMT` | Gold materializer |
| `TC-WH` | Analytical warehouse queries |
| `TC-FE-CTL` | Frontend controller and view |
| `TC-FE-SVC` | Frontend service |

</details>

<br>

<h1 id="bar_chart-coverage-summary">📊 Coverage Summary</h1>

| Area | Tool | Coverage |
|---|---|---|
| Backend | pytest-cov (statements + branches) | **98%** — 1,058 statements, 222 branches |
| Frontend | JaCoCo | **82%** instructions · **73%** lines · **100%** branches |

<details>
  <summary><b>Backend coverage by module</b></summary>

| Backend module | Coverage |
|---|---|
| `transformation/silver.py` | 99% |
| `ingestion/ingestion.py` | 99% |
| `ingestion/bronze.py` | 98% |
| `transformation/gold.py` | 97% |
| `ingestion/jurisprudencia.py` | 95% |
| `main.py` | 93% |
| `warehouse/postgres.py`, `ingestion/storage.py`, `infra/database/*`, Gold recipes | 100% |

</details>

<details>
  <summary><b>Frontend coverage by class</b></summary>

| Frontend class | Line coverage | Note |
|---|---|---|
| `ProcessoController` | 100% | All 4 branches covered |
| `ProcessoService` | 100% | |
| `DatalawApplication` | 33% | `main` requires a database (integration level) |
| `Processo` | 0% | Getters and setters only |
| `ProcessoDTOResponse` | 0% | Single-line record |

All classes that contain logic are fully covered in the frontend.

</details>

<br>

<h1 id="test_tube-backend-test-cases">🧪 Backend Test Cases</h1>

<p align="justify">
Python test suite located in <code>backend/tests</code>, executed with pytest. The <b>Inputs</b> column shows how many times a parametrized test case runs.
</p>

<details>
  <summary><b>Database Infrastructure</b> (5 test cases)</summary>

**Files:** `tests/infra/database/model/bronze/test_bronze_process.py`, `tests/infra/database/test_session.py`, `tests/test_smoke.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-INF-001 | `test_datajud_extract_mapping` | Inspect the `BronzeDataJudExtract` ORM table | Table `bronze.datajud_extract` with the expected columns, UUID primary key with default, `JSONB` payload and 64-char hash | 1 |
| TC-INF-002 | `test_ingestion_state_mapping` | Inspect the ingestion checkpoint ORM table | Table `bronze.datajud_ingestion_state` with the expected columns and `tribunal_alias` as primary key | 1 |
| TC-INF-003 | `test_create_session_factory_uses_given_settings` | Build a session factory from explicit settings | `sessionmaker` bound to the configured URL with `expire_on_commit=False`, without connecting | 1 |
| TC-INF-004 | `test_create_session_factory_reads_database_url_from_environment` | Build a session factory with `DATABASE_URL` set in the environment | The engine uses the URL from the environment | 1 |
| TC-SMK-001 | `test_smoke` | Run the test suite bootstrap | pytest discovers and runs tests | 1 |

</details>

<details>
  <summary><b>Bronze Layer</b> (14 test cases)</summary>

**File:** `tests/ingestion/test_bronze.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-BRZ-001 | `test_payload_hash_is_stable_for_key_order` | Hash two payloads with the same content in different key order | Identical hashes | 1 |
| TC-BRZ-002 | `test_process_raw_file_builds_one_upsert_per_process` | Process a raw file with two processes, one new and one unchanged | One upsert per process, `changed=1`, `unchanged=1`, single transaction | 1 |
| TC-BRZ-003 | `test_invalid_process_without_datajud_id_stops_file_processing` | Read a file whose process has no `id` | `BronzeProcessingError` mentioning `_source.id` | 1 |
| TC-BRZ-004 | `test_read_process_payloads_reads_gzip_files` | Read a `.json.gz` raw page | Process payloads are returned | 1 |
| TC-BRZ-005 | `test_read_process_payloads_rejects_malformed_responses` | Read invalid JSON, non-object document, missing `hits.hits`, hit without `_source`, blank or numeric `id` | `BronzeProcessingError` with a specific message for each case | 8 |
| TC-BRZ-006 | `test_metadata_for_file_resolves_tribunal_case_insensitively` | Resolve tribunal metadata from a `TJSP/` folder | Alias `api_publica_tjsp` and acronym `TJSP` | 1 |
| TC-BRZ-007 | `test_metadata_for_file_rejects_unknown_layouts` | File directly under the raw folder, or under an unmapped tribunal | `BronzeProcessingError` | 2 |
| TC-BRZ-008 | `test_metadata_for_file_rejects_files_outside_raw_directory` | File outside the raw directory | `BronzeProcessingError` "Arquivo fora de" | 1 |
| TC-BRZ-009 | `test_process_raw_file_keeps_only_included_processes` | Process a file with `included_datajud_ids` selecting one of three processes | Only the selected process is upserted, with the given extraction timestamp | 1 |
| TC-BRZ-010 | `test_process_raw_file_without_selected_processes_changes_nothing` | Process a file with an empty selection | Nothing is written, totals are zero | 1 |
| TC-BRZ-011 | `test_process_raw_directory_processes_json_files_in_lexical_order` | Directory with `.json`, `.json.gz` and unrelated files | JSON files processed in lexical order, one session each; other files ignored | 1 |
| TC-BRZ-012 | `test_process_raw_directory_stops_at_first_invalid_file` | First file is invalid | Processing stops with an error and nothing is written | 1 |
| TC-BRZ-013 | `test_bronze_main_processes_files_and_syncs_silver` | Run the Bronze command-line entry point | Files are processed, Silver is synchronized and a summary is printed | 1 |
| TC-BRZ-014 | `test_postgres_merge_updates_only_changed_process` | **Integration:** upsert the same process three times against PostgreSQL | Inserted, then unchanged, then updated only when the payload changes (skipped without `DATABASE_URL`) | 1 |

</details>

<details>
  <summary><b>DataJud Ingestion</b> (25 test cases)</summary>

**Files:** `tests/ingestion/test_incremental_ingestion.py`, `tests/ingestion/test_ingestion_helpers.py`, `tests/ingestion/test_ingestion.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-ING-001 | `test_full_load_persists_only_completion_in_the_same_movement` | Historical load with one real completion and one false positive | Only the process with a completion movement in the window is persisted; date filter starts on 2026-03-01; pagination uses `search_after` | 1 |
| TC-ING-002 | `test_incremental_load_updates_known_process_and_new_completion` | Incremental load with a known process and a new completion | Both are persisted; filter on `@timestamp`; checkpoint advances | 1 |
| TC-ING-003 | `test_incremental_load_requires_a_completed_historical_load` | Incremental load without a checkpoint | `InitialIngestionRequiredError` asking for `full-ingest` | 1 |
| TC-ING-004 | `test_full_load_logs_progress_and_summary` | Run a historical load with logging enabled | Start, page progress, Bronze summary, checkpoint and final summary are logged | 1 |
| TC-ING-005 | `test_service_rejects_unknown_tribunal` | Create the service for an unmapped tribunal | `ValueError` "Tribunal não configurado" | 1 |
| TC-ING-006 | `test_service_rejects_non_positive_page_size` | Create the service with page size 0 or negative | `ValueError` | 2 |
| TC-ING-007 | `test_page_without_selected_processes_is_saved_but_not_persisted` | Page whose processes have no completion | Page counted, nothing persisted, checkpoint saved | 1 |
| TC-ING-008 | `test_full_load_runs_silver_sync_and_reports_its_totals` | Historical load with Silver sync configured | Report contains the Silver totals | 1 |
| TC-ING-009 | `test_full_load_stops_when_datajud_times_out` | DataJud returns `timed_out=true` | `DataJudIngestionError` and no checkpoint saved | 1 |
| TC-ING-010 | `test_full_page_without_sort_cursor_stops_pagination` | Full page without the `sort` cursor | `DataJudIngestionError` and no checkpoint saved | 1 |
| TC-ING-011 | `test_incremental_load_keeps_naive_checkpoint_as_utc` | Checkpoint stored without timezone | Treated as UTC when building the query window | 1 |
| TC-ING-012 | `test_response_hits_returns_hit_list` | Valid DataJud response | Hit list returned | 1 |
| TC-ING-013 | `test_response_hits_rejects_invalid_responses` | Timed-out response, missing or malformed `hits.hits` | `DataJudIngestionError` | 5 |
| TC-ING-014 | `test_source_payloads_rejects_hits_without_valid_source` | Hit without `_source`, or with a blank/numeric `id` | `DataJudIngestionError` identifying the hit position | 4 |
| TC-ING-015 | `test_source_payloads_returns_sources_in_order` | Valid hits | Sources returned in the original order | 1 |
| TC-ING-016 | `test_last_sort_value_requires_two_part_cursor` | Missing, non-list or wrong-size `sort` | `DataJudIngestionError` about the pagination cursor | 4 |
| TC-ING-017 | `test_last_sort_value_returns_cursor` | Valid two-part `sort` | Cursor returned | 1 |
| TC-ING-018 | `test_has_completion_in_window_ignores_invalid_or_outside_movements` | No movements, invalid items, non-completion codes, invalid dates, dates outside the window | Returns `False` | 9 |
| TC-ING-019 | `test_has_completion_in_window_accepts_completion_inside_window` | Completion code (22/246) inside the window, with or without timezone | Returns `True` | 4 |
| TC-ING-020 | `test_subtract_calendar_months_clamps_to_month_end` | Subtract months across years, from the 31st, in leap years and zero months | Correct date, clamped to the last day of the month | 5 |
| TC-ING-021 | `test_as_utc_assumes_utc_for_naive_values` | Datetime without timezone | Same instant with UTC timezone | 1 |
| TC-ING-022 | `test_as_utc_converts_aware_values` | Datetime in UTC-3 | Converted to UTC | 1 |
| TC-ING-023 | `test_ingestion_report_counts_unchanged_processes` | Report with persisted and changed totals | `unchanged = persisted − changed` | 1 |
| TC-API-001 | `test_ingest_returns_json_and_calls_correct_url` | Call the DataJud client | POST to `/<tribunal>/_search` with API key header and 90 s timeout; JSON returned | 1 |
| TC-API-002 | `test_ingest_retries_after_failure_and_then_succeeds` | First request fails with a network error | Request is retried and succeeds | 1 |

</details>

<details>
  <summary><b>Raw Storage</b> (2 test cases)</summary>

**File:** `tests/ingestion/test_storage.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-STO-001 | `test_save_raw_response_writes_a_partitioned_gzip_file` | Save a response page | File written at `tjsp/ingestion_date=.../run_id=.../page-000001.json.gz` with the same content | 1 |
| TC-STO-002 | `test_save_raw_response_removes_partial_file_when_serialization_fails` | Payload that cannot be serialized | Error raised and no partial file left behind | 1 |

</details>

<details>
  <summary><b>Jurisprudence and Precedents (BNP)</b> (18 test cases)</summary>

**File:** `tests/ingestion/test_jurisprudencia.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-JUR-001 | `test_clean_html_removes_tags_entities_and_extra_whitespace` | `None`, empty text, HTML tags, escaped entities and line breaks | Plain text with single spaces (`""` for empty input) | 4 |
| TC-JUR-002 | `test_source_hash_uses_only_key_fields_and_is_order_independent` | Hash precedents with extra fields and different key order | Hash depends only on the key fields | 1 |
| TC-JUR-003 | `test_sanitize_term_drops_short_tokens_generic_prefix_and_limits_size` | Subject names with the generic prefix "Direito", punctuation, short words and many words | Prefix and short tokens removed, punctuation stripped, at most four words (e.g. "DIREITO DO CONSUMIDOR" → "CONSUMIDOR") | 7 |
| TC-JUR-004 | `test_buscar_skips_request_for_blank_term` | Empty or blank search term | No HTTP request; empty list | 2 |
| TC-JUR-005 | `test_buscar_sends_filter_payload_and_returns_results` | Valid search term | POST with the BNP filter payload; results returned | 1 |
| TC-JUR-006 | `test_buscar_uses_given_courts_and_types` | Search with explicit courts and precedent types | Payload uses the given filters | 1 |
| TC-JUR-007 | `test_buscar_returns_empty_list_for_non_200_status` | BNP returns a non-200 status | Empty list, warning logged | 1 |
| TC-JUR-008 | `test_buscar_returns_empty_list_on_network_error` | Network failure | Empty list, no exception | 1 |
| TC-JUR-009 | `test_buscar_returns_empty_list_when_body_has_no_results` | Response without `resultados` | Empty list | 1 |
| TC-JUR-010 | `test_fetch_skips_search_when_sanitized_term_is_empty` | Subject name that becomes empty after sanitization | No search; returns 0 | 1 |
| TC-JUR-011 | `test_fetch_returns_zero_without_opening_session_when_no_results` | BNP returns no results | Returns 0 without opening a database session | 1 |
| TC-JUR-012 | `test_fetch_persists_precedent_with_cleaned_text` | BNP returns a precedent with HTML | Precedent saved in Silver with cleaned thesis and question | 1 |
| TC-JUR-013 | `test_fetch_skips_precedent_already_saved` | Precedent with an existing source hash | Not inserted again | 1 |
| TC-JUR-014 | `test_fetch_skips_precedent_without_thesis_or_question` | Precedent without thesis and question | Ignored | 1 |
| TC-JUR-015 | `test_fetch_truncates_title_to_250_characters` | Very long question text | Title truncated to 250 characters | 1 |
| TC-JUR-016 | `test_fetch_uses_fallbacks_for_missing_fields` | Precedents without number, court, question or id | Identifier falls back to the BNP id or "Precedente", court to `CNJ`, title to "<identifier> - <subject>" and summary to the thesis | 1 |
| TC-JUR-017 | `test_sync_all_active_subjects_fetches_each_frequent_subject` | Subjects with at least 30 processes | One BNP lookup per subject; totals reported | 1 |
| TC-JUR-018 | `test_sync_all_active_subjects_with_no_subjects` | No qualifying subjects | No lookup; zero totals | 1 |

</details>

<details>
  <summary><b>Command-Line Entry Point</b> (5 test cases)</summary>

**File:** `tests/test_main.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-CLI-001 | `test_main_runs_incremental_ingestion_by_default` | Run `data_law.main` without arguments | Incremental ingestion runs and the summary is printed | 1 |
| TC-CLI-002 | `test_main_runs_full_ingestion_with_flag` | Run with `--full` | Historical ingestion runs | 1 |
| TC-CLI-003 | `test_main_wires_silver_sync_to_the_same_session_factory` | Trigger the configured Silver sync | Silver sync uses the same session factory as the ingestion | 1 |
| TC-CLI-004 | `test_main_logs_and_reraises_ingestion_errors` | Ingestion raises an error | Error logged and re-raised; no summary printed | 1 |
| TC-CLI-005 | `test_configure_logging_uses_log_level_from_environment` | `LOG_LEVEL=debug` | Logging configured with level `DEBUG` | 1 |

</details>

<details>
  <summary><b>Silver Layer Transformations</b> (23 test cases)</summary>

**Files:** `tests/transformation/test_silver.py`, `tests/transformation/test_gold.py` (subject extraction)  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-SLV-001 | `test_string_strips_text_and_converts_numbers` | Text with spaces, blank or empty text, numbers, booleans, lists and `None` | Trimmed text, numbers as text, `None` for blank values and other types | 8 |
| TC-SLV-002 | `test_integer_accepts_only_integers_and_numeric_strings` | Integers, numeric strings (with spaces), decimals, booleans, invalid text and `None` | Integer for integers and numeric strings, `None` otherwise | 9 |
| TC-SLV-003 | `test_mapping_returns_same_dict` | Dictionary input | Same dictionary | 1 |
| TC-SLV-004 | `test_mapping_returns_empty_dict_for_non_dict` | `None`, list, text, number | Empty dictionary | 4 |
| TC-SLV-005 | `test_canonical_hash_ignores_key_order_and_keeps_unicode` | Same object with different key order and accents | Same SHA-256 hash | 1 |
| TC-SLV-006 | `test_canonical_hash_rejects_nan` | Object containing `NaN` | `ValueError` | 1 |
| TC-SLV-007 | `test_assign_sets_every_value_on_instance` | Assign a dictionary to an object | Every attribute updated | 1 |
| TC-SLV-008 | `test_parse_process_date_accepts_datajud_formats` | `YYYYMMDDHHMMSS`, `YYYYMMDD` and ISO dates | Correct `date` | 5 |
| TC-SLV-009 | `test_parse_process_date_ignores_missing_values_without_warning` | `None`, blank or non-text values | `None` and no warning | 4 |
| TC-SLV-010 | `test_parse_process_date_warns_once_on_invalid_value` | Invalid dates | `None` and exactly one warning | 5 |
| TC-SLV-011 | `test_parse_timestamp_normalizes_to_utc` | Timestamps with `Z`, offsets or no timezone | UTC `datetime` | 5 |
| TC-SLV-012 | `test_parse_timestamp_ignores_missing_values_without_warning` | `None`, blank or non-text values | `None` and no warning | 5 |
| TC-SLV-013 | `test_parse_timestamp_warns_on_invalid_value` | Invalid timestamps | `None` and one warning | 3 |
| TC-SLV-014 | `test_process_values_maps_datajud_payload` | Complete DataJud payload | Every Silver process column filled from the payload and the Bronze extract | 1 |
| TC-SLV-015 | `test_process_values_tolerates_missing_and_malformed_fields` | Payload with missing and malformed fields | `None` for those columns and warnings for invalid dates | 1 |
| TC-SLV-016 | `test_movement_values_maps_fields` | Valid movement | Code, name, UTC date, court and complements mapped | 1 |
| TC-SLV-017 | `test_movement_values_without_movements` | Payload without `movimentos` | Empty list, no warning | 1 |
| TC-SLV-018 | `test_movement_values_rejects_non_list` | `movimentos` is not a list | Empty list and warning | 1 |
| TC-SLV-019 | `test_movement_values_skips_duplicates_and_invalid_items` | Duplicated and invalid movements | Duplicates removed, invalid items ignored with warning | 1 |
| TC-SLV-020 | `test_subject_values_without_subjects` | Payload without `assuntos` | Empty list, no warning | 1 |
| TC-SLV-021 | `test_subject_values_rejects_non_list` | `assuntos` is not a list | Empty list and warning | 1 |
| TC-SLV-022 | `test_subject_values_accepts_only_boolean_principal` | `principal` with boolean and non-boolean values | Only booleans kept; others become `None` | 1 |
| TC-SLV-023 | `test_subject_extraction_and_canonical_hashing` | Subjects with duplicates, numeric-string code and an invalid item | Two unique subjects, code converted, one warning, canonical hash | 1 |

</details>

<details>
  <summary><b>Bronze → Silver Synchronization</b> (13 test cases)</summary>

**File:** `tests/transformation/test_silver_sync.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-SYN-001 | `test_rejects_non_positive_batch_size` | Batch size 0 | `ValueError` | 1 |
| TC-SYN-002 | `test_returns_empty_report_when_nothing_is_pending` | No pending Bronze extracts | Report with zero totals | 1 |
| TC-SYN-003 | `test_inserts_new_process_with_movements_and_subjects` | New Bronze extract | Process, movements and subjects inserted in Silver | 1 |
| TC-SYN-004 | `test_skips_process_whose_payload_hash_did_not_change` | Extract already synchronized with the same hash | Process not rewritten | 1 |
| TC-SYN-005 | `test_updates_changed_process_and_replaces_stale_children` | Extract with a new payload | Process updated; removed movements and subjects deleted | 1 |
| TC-SYN-006 | `test_removes_all_children_when_payload_has_none` | New payload without movements and subjects | All children deleted | 1 |
| TC-SYN-007 | `test_ignores_extract_that_no_longer_exists` | Pending extract deleted before processing | Skipped without error | 1 |
| TC-SYN-008 | `test_counts_and_prints_warnings` | Payload with invalid fields | Warnings printed and counted in the report | 1 |
| TC-SYN-009 | `test_processes_every_pending_batch` | More pending extracts than the batch size | All batches processed | 1 |
| TC-SYN-010 | `test_pending_bronze_ids_selects_missing_or_changed_extracts` | Mix of new, changed and synchronized extracts | Only new or changed extracts selected | 1 |
| TC-SYN-011 | `test_searches_precedents_for_each_new_subject` | New subjects inserted | One precedent lookup per new subject | 1 |
| TC-SYN-012 | `test_skips_precedent_search_for_subject_without_code_or_name` | Subject without code or name | No precedent lookup | 1 |
| TC-SYN-013 | `test_precedent_search_failure_does_not_stop_sync` | Precedent lookup raises an error | Synchronization continues | 1 |

</details>

<details>
  <summary><b>Gold Recipe Registry and Recipes</b> (8 test cases)</summary>

**File:** `tests/transformation/test_gold.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-GLD-001 | `test_registry_registers_sql_and_polars_recipes` | Register SQL and Polars recipes | Both available by name | 1 |
| TC-GLD-002 | `test_registry_rejects_duplicate_and_missing_names` | Register a duplicated name, select an unknown name | `GoldConfigurationError` ("duplicada" / "nao encontrada") | 1 |
| TC-GLD-003 | `test_registry_accepts_readonly_cte_from_silver` | Read-only query with CTEs over `silver` | Accepted | 1 |
| TC-GLD-004 | `test_registry_rejects_non_readonly_or_non_silver_sql` | DML, DDL or tables outside `silver` | `GoldConfigurationError` | 5 |
| TC-GLD-005 | `test_polars_output_requires_valid_nonempty_columns` | DataFrame without columns or with invalid names | `GoldExecutionError` | 1 |
| TC-GLD-006 | `test_success_by_class_recipe_is_registered` | Load project recipes | `process_results` registered as a SQL recipe over Silver | 1 |
| TC-GLD-007 | `test_success_by_topic_recipe_is_registered` | Load project recipes | `topic_results` registered as SQL, reading processes, subjects and movements, with the weighted success rate and the `COUNT(*) >= 30` threshold | 1 |
| TC-GLD-008 | `test_topic_precedents_recipe_is_registered` | Load project recipes | `topic_precedents` registered | 1 |

</details>

<details>
  <summary><b>Gold Materializer</b> (23 test cases)</summary>

**File:** `tests/transformation/test_gold_materializer.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-GMT-001 | `test_materialization_rejects_invalid_configuration` | Unsupported refresh mode, SQL without query, Polars without transform, unknown engine | `GoldConfigurationError` | 6 |
| TC-GMT-002 | `test_materialization_rejects_invalid_table_name` | Uppercase letter, leading digit, hyphen, empty name, 64-character name | `GoldConfigurationError` | 5 |
| TC-GMT-003 | `test_sql_recipe_rejects_unsafe_or_invalid_query` | Empty or blank query, invalid syntax, two statements, `UPDATE`, data-modifying CTEs (`INSERT`/`UPDATE`), joins or subqueries on `gold`/`public` | `GoldConfigurationError` with a specific message | 9 |
| TC-GMT-004 | `test_sql_recipe_accepts_query_without_tables` | Constant `SELECT` | Accepted | 1 |
| TC-GMT-005 | `test_sql_recipe_creates_new_table_from_staging` | First run of a SQL recipe | Staging table created and renamed to the target; row count reported | 1 |
| TC-GMT-006 | `test_sql_recipe_swaps_existing_table_and_drops_old_copy` | Target table already exists | Old table renamed and dropped after the swap | 1 |
| TC-GMT-007 | `test_polars_recipe_writes_dataframe_to_staging` | Polars recipe returning a DataFrame | DataFrame written to staging and swapped | 1 |
| TC-GMT-008 | `test_polars_recipe_accepts_lazy_frame` | Polars recipe returning a LazyFrame | Collected and written | 1 |
| TC-GMT-009 | `test_polars_recipe_must_return_a_frame` | Transform returns `None`, a list or a dictionary | `GoldExecutionError` | 3 |
| TC-GMT-010 | `test_polars_recipe_with_invalid_columns_writes_nothing` | DataFrame without columns, or with uppercase or space in a column name | `GoldExecutionError` and no table written | 3 |
| TC-GMT-011 | `test_polars_frame_with_duplicate_columns_is_rejected` | Frame with duplicated column names | `GoldExecutionError` "duplicadas" | 1 |
| TC-GMT-012 | `test_context_reads_silver_with_polars` | Read a Silver query through the context | `polars.read_database` called with the connection | 1 |
| TC-GMT-013 | `test_context_rejects_reading_outside_silver` | Read a query outside `silver` | `GoldConfigurationError` | 1 |
| TC-GMT-014 | `test_each_recipe_runs_in_its_own_transaction` | Run several recipes | One transaction per recipe | 1 |
| TC-GMT-015 | `test_failed_recipe_keeps_previous_table_and_earlier_results` | Second recipe fails | Its transaction is rolled back; previous table and earlier recipes preserved | 1 |
| TC-GMT-016 | `test_run_by_name_only_materializes_selected_recipe` | Run with a recipe name | Only that recipe runs | 1 |
| TC-GMT-017 | `test_run_with_unknown_name_fails_before_touching_database` | Run with an unknown name | Error raised before any statement | 1 |
| TC-GMT-018 | `test_materializer_uses_default_registry` | Create the materializer without a registry | Default registry used | 1 |
| TC-GMT-019 | `test_materializer_creates_engine_from_settings` | Create the materializer without an engine | Engine created from `DATABASE_URL` | 1 |
| TC-GMT-020 | `test_identifier_helpers_quote_and_validate` | Quote and qualify identifiers | Quoted `"gold"."name"`; invalid names rejected | 1 |
| TC-GMT-021 | `test_temporary_names_are_unique_valid_identifiers` | Generate temporary table names | Unique and valid PostgreSQL identifiers | 1 |
| TC-GMT-022 | `test_main_runs_materializer_and_prints_report` | Run the Gold command with `--name` | Selected recipe materialized; report printed | 1 |
| TC-GMT-023 | `test_main_without_name_runs_every_recipe` | Run the Gold command without arguments | Every registered recipe materialized | 1 |

</details>

<details>
  <summary><b>Analytical Warehouse</b> (7 test cases)</summary>

**File:** `tests/warehouse/test_postgres.py`  

| ID | Test | Scenario | Expected Result | Inputs |
|---|---|---|---|---|
| TC-WH-001 | `test_validate_limit_rejects_non_positive_values` | Limit 0 or negative | `ValueError` | 2 |
| TC-WH-002 | `test_validate_limit_accepts_positive_values` | Limit 1 | Accepted | 1 |
| TC-WH-003 | `test_warehouse_uses_default_session_factory` | Create the warehouse without a session factory | Default factory used | 1 |
| TC-WH-004 | `test_list_processes_maps_rows_to_summaries` | List processes of a tribunal | Rows mapped to `ProcessSummary`; SQL filters by tribunal, orders `DESC NULLS LAST` and applies the limit | 1 |
| TC-WH-005 | `test_list_processes_rejects_invalid_limit_before_querying` | List with limit 0 | `ValueError` and no query executed | 1 |
| TC-WH-006 | `test_count_processes_by_class_maps_rows_to_counts` | Count processes by class | Rows mapped to `ProcessCountByClass`; SQL uses `coalesce(..., 'Não informada')`, `GROUP BY` and the limit | 1 |
| TC-WH-007 | `test_count_processes_by_class_rejects_invalid_limit` | Count with a negative limit | `ValueError` and no query executed | 1 |

</details>

<br>

<h1 id="test_tube-frontend-test-cases">🧪 Frontend Test Cases</h1>

<p align="justify">
Java test suite located in <code>frontend/src/test</code>, executed with JUnit 5. Controller tests use <code>@WebMvcTest</code> and render the Thymeleaf template; service tests use Mockito.
</p>

<details>
  <summary><b>Controller and View</b> (8 test cases)</summary>

**File:** `frontend/src/test/java/com/datatech/datalaw/controller/ProcessoControllerTest.java`  
**Type:** `@WebMvcTest` with `ProcessoService` mocked; the Thymeleaf template is rendered.  

| ID | Test | Scenario | Expected Result |
|---|---|---|---|
| TC-FE-CTL-001 | `raizSemFiltroUsaClasseVaziaERenderizaPagina` | `GET /` without filters | Status 200, view `orgaos-julgadores`, empty filters, lists in the model, title "Visão Geral dos Processos" |
| TC-FE-CTL-002 | `filtroPorClasseRepassaClasseAoServicoEMostraTitulo` | `GET /processos/orgaos-julgadores?classeNome=Execução Fiscal` | Class passed to the service; court shown on the page |
| TC-FE-CTL-003 | `paginaRenderizaSemDados` | Filter with no data | Status 200 and the page is rendered |
| TC-FE-CTL-004 | `filtroPorTemaEClasseRepassaAmbosAoServicoEMostraTitulo` | Filter by subject and class | Both filters passed to the service; title "Tema: … · Classe: …" |
| TC-FE-CTL-005 | `taxaSucessoRetornaJsonComTaxa` | `GET /processos/taxa-sucesso?classeNome=…` | JSON `{"taxa": 62.5}` |
| TC-FE-CTL-006 | `taxaSucessoSemClasseRetornaBadRequest` | Success rate without `classeNome` | Status 400 and the service is not called |
| TC-FE-CTL-007 | `taxaSucessoTemaRetornaJsonComTaxaEPrecedentes` | `GET /processos/taxa-sucesso-tema?assuntoNome=Dano Moral` | JSON with the rate and the list of precedents |
| TC-FE-CTL-008 | `taxaSucessoTemaSemAssuntoRetornaBadRequest` | Subject success rate without `assuntoNome` | Status 400 and the service is not called |

</details>

<details>
  <summary><b>Service</b> (6 test cases)</summary>

**File:** `frontend/src/test/java/com/datatech/datalaw/service/ProcessoServiceTest.java`  
**Type:** Mockito unit test with `ProcessoRepository` mocked.  

| ID | Test | Scenario | Expected Result |
|---|---|---|---|
| TC-FE-SVC-001 | `quantidadePorOrgaoJulgadorRepassaFiltroDeClasseEAssunto` | Count processes by court with class and subject filters | Repository called with both filters; same list returned |
| TC-FE-SVC-002 | `quantidadePorClasseRetornaResultadoDoRepositorio` | Count processes by class | Repository result returned |
| TC-FE-SVC-003 | `quantidadePorAssuntoRetornaResultadoDoRepositorio` | Count processes by subject | Repository result returned |
| TC-FE-SVC-004 | `taxaSucessoPorClasseRetornaValorDoRepositorio` | Success rate by class | Repository value returned |
| TC-FE-SVC-005 | `taxaSucessoPorAssuntoRetornaValorDoRepositorio` | Success rate by subject | Repository value returned |
| TC-FE-SVC-006 | `precedentesPorAssuntoRetornaResultadoDoRepositorio` | Precedents by subject | Repository result returned |

</details>

<br>

<h1 id="warning-known-gaps">⚠️ Known Gaps</h1>

<p align="justify">
The items below are not covered by the current unit tests. Most of them depend on a real PostgreSQL database and are planned as integration tests.
</p>

| Item | Reason | Planned Coverage |
|---|---|---|
| SQL of the Gold recipes (`process_results`, `topic_results`, `topic_precedents`) | Executed only by PostgreSQL; unit tests validate registration and safety rules | Integration tests with Testcontainers |
| Native queries of `ProcessoRepository` (frontend) | The repository is mocked in unit tests | `@DataJpaTest` with Testcontainers |
| Alembic migrations | Require a real database | Integration tests |
| `test_postgres_merge_updates_only_changed_process` | Skipped when `DATABASE_URL` is not set | Run against a disposable database only |
| Conditional states of the `orgaos-julgadores` template (title with a single filter, empty-state messages, "clear filters" button, HTML escaping) | Not asserted by the current controller tests | Additional `@WebMvcTest` cases |
| Success-rate endpoints when Gold has no data (`taxa: null`, empty precedent list) | Not asserted by the current controller tests | Additional `@WebMvcTest` cases |
| Frontend getters/setters (`Processo`, `ProcessoDTOResponse`) and `DatalawApplication.main` | No business logic | Not planned |

<br>

<h1 id="robot-continuous-integration">🤖 Continuous Integration</h1>

<p align="justify">
The test suites were validated in Linux containers matching the CI runner (<code>ubuntu-latest</code>):
</p>

| Check | Environment | Result |
|---|---|---|
| `uv run pytest` | Python 3.12 | Passes (skipped tests do not fail the build) |
| `./mvnw test` | JDK 21 | Passes |
| `./mvnw clean package -DskipTests` (current CI step) | JDK 21 | Passes |

<p align="justify">
When the tests are added to the pipeline, the job must <b>not</b> define <code>DATABASE_URL</code>, so the integration test is skipped instead of writing to a shared database.
</p>

<br>

<p align="center">
© 2026 — DataTech / DataLaw Project</p>
<p align="center">
Developed in the educational context of Fatec São Paulo, in partnership with Xertica.
</p>
