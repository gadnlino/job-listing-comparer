## ADDED Requirements

### Requirement: Comprehensive pytest test suite

The system SHALL include a pytest test suite covering all capabilities: resume parsing, job collection, job matching, report generation, and web application. Every spec scenario MUST have a corresponding test case.

#### Scenario: Test suite runs offline

- **WHEN** the developer runs `pytest`
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, or Ollama

#### Scenario: External HTTP mocked in tests

- **WHEN** tests exercise job collectors or the LLM summarizer
- **THEN** all external HTTP requests are mocked using fixture JSON payloads

### Requirement: Resume parsing tests

The system SHALL include tests for PDF parsing and skill extraction covering all resume-parsing spec scenarios.

#### Scenario: PDF parser tests

- **WHEN** `tests/test_resume_parser.py` runs
- **THEN** it covers valid PDF extraction, invalid PDF handling, and empty text handling

#### Scenario: Skill extractor tests

- **WHEN** `tests/test_skill_extractor.py` runs
- **THEN** it covers known skill detection, alias matching, JavaScript≠Java, deduplication, confidence tiers, excluded tokens, and DetectedSkill output shape

### Requirement: Job collection tests

The system SHALL include tests for collectors, orchestration, and normalization covering all job-collection spec scenarios.

#### Scenario: Collector normalization tests

- **WHEN** `tests/test_collectors.py` runs
- **THEN** it covers Remotive, Adzuna, and Arbeitnow payload normalization using fixture JSON

#### Scenario: Remotive batch fetch test

- **WHEN** the Remotive collector is tested
- **THEN** the test verifies exactly one API call is made per fetch operation

#### Scenario: Adzuna credential skip test

- **WHEN** Adzuna credentials are missing in the test environment
- **THEN** the collector returns an empty result and a warning without raising an exception

#### Scenario: Orchestrator fault tolerance test

- **WHEN** `tests/test_orchestrator.py` runs
- **THEN** it covers multi-source collection, per-source error isolation, zero-config mode, and client-side query filtering

#### Scenario: Job deduplication test

- **WHEN** `tests/test_normalizer.py` runs
- **THEN** it covers deduplication by URL and fallback by title+company

### Requirement: Job matching tests

The system SHALL include tests for track classification, fit scoring, and market aggregation covering all job-matching spec scenarios.

#### Scenario: Track classifier tests

- **WHEN** `tests/test_track_classifier.py` runs
- **THEN** it covers multi-track assignment and primary track selection

#### Scenario: Matcher tests

- **WHEN** `tests/test_matcher.py` runs
- **THEN** it covers fit score bounds, weight tiers, parent/child dedup, seniority estimation, and shared extractor on job title+description

#### Scenario: Market aggregation tests

- **WHEN** `tests/test_aggregator.py` runs
- **THEN** it covers top requested skills ranking and top missing skills ranking

### Requirement: Report generation tests

The system SHALL include tests for all report outputs and the LLM summarizer covering all report-generation spec scenarios.

#### Scenario: Report context tests

- **WHEN** `tests/test_report_context.py` runs
- **THEN** it verifies ReportSummaryContext contains only structured fields, excludes job descriptions, and filters top 20 jobs by fit score

#### Scenario: CSV report tests

- **WHEN** `tests/test_report_csv.py` runs
- **THEN** it verifies required columns and fit_score descending sort order

#### Scenario: Markdown report tests

- **WHEN** `tests/test_report_markdown.py` runs
- **THEN** it verifies all required sections and deterministic study recommendation logic

#### Scenario: LLM summarizer tests

- **WHEN** `tests/test_llm_summarizer.py` runs
- **THEN** it verifies the prompt contains only structured JSON, never raw job descriptions, and template fallback works when Ollama fails

#### Scenario: PDF report tests

- **WHEN** `tests/test_report_pdf.py` runs
- **THEN** it verifies PDF file creation with required sections and skips generation when no jobs are found

### Requirement: Web application tests

The system SHALL include tests for all HTTP routes and UI warnings covering all web-app spec scenarios.

#### Scenario: Web route tests

- **WHEN** `tests/test_web_app.py` runs with FastAPI TestClient
- **THEN** it covers GET /, POST /analyze (valid PDF and non-PDF rejection), download endpoints, and friendly 404 when reports are missing

#### Scenario: Results page content tests

- **WHEN** POST /analyze completes successfully in tests
- **THEN** the response includes resume skills, job table, source warnings, Adzuna skipped warning, Remotive attribution, download links, and PDF auto-open script when PDF was generated

#### Scenario: PDF auto-open HTML contract tests

- **WHEN** POST /analyze completes with a generated PDF
- **THEN** the results HTML contains the auto-open script targeting `/download/market_fit_report.pdf` and a popup-blocked fallback element

#### Scenario: No auto-open when PDF absent

- **WHEN** POST /analyze completes with zero job matches
- **THEN** the results HTML does not contain the PDF auto-open script

### Requirement: Integration pipeline test

The system SHALL include at least one integration test that exercises the full analysis pipeline with all external services mocked.

#### Scenario: Full pipeline integration test

- **WHEN** `tests/test_integration_pipeline.py` runs
- **THEN** it uploads a fixture PDF, mocks all job APIs and Ollama, runs POST /analyze, and verifies reports are written and results page is rendered

### Requirement: Test fixtures and configuration

The system SHALL provide shared test fixtures and pytest configuration.

#### Scenario: Shared fixtures available

- **WHEN** any test module runs
- **THEN** `tests/conftest.py` provides fixtures including a sample PDF, API response JSON payloads, and isolated temporary data/report directories

#### Scenario: Pytest configuration documented

- **WHEN** a developer reads the README
- **THEN** it documents how to run the test suite with `pytest`
