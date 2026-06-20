# Testing

Pytest suite validating application capabilities without live external services.

## Requirements

### Requirement: Streaming analyze endpoint tests

The system SHALL include tests for the NDJSON streaming analyze endpoint with mocked pipeline dependencies.

#### Scenario: Stream emits progress and done events

- **WHEN** `tests/test_analyze_stream.py` POSTs to `/analyze/stream` with a valid PDF and mocked externals
- **THEN** the response body contains at least one `type: progress` NDJSON line and a final `type: done` line with a redirect URL

#### Scenario: Stream emits error on invalid PDF

- **WHEN** the stream test POSTs a non-PDF file
- **THEN** the response contains a `type: error` NDJSON line or an appropriate HTTP error

#### Scenario: Link validation progress in stream

- **WHEN** the stream test runs with link validation enabled and mocked HTTP
- **THEN** at least one progress line includes `stage: validate` with title and source fields

### Requirement: Analysis loading indicator tests

The system SHALL include tests verifying the home page loading indicator and streaming submit contract.

#### Scenario: Home page includes loading indicator elements

- **WHEN** `tests/test_web_app.py` requests `GET /`
- **THEN** the response HTML includes the loading indicator container and status message element

#### Scenario: Home page includes streaming submit script

- **WHEN** the home page test runs
- **THEN** the response HTML includes client-side script that submits via fetch to `/analyze/stream` and updates the loading indicator from NDJSON progress events

### Requirement: Link validator unit tests

The system SHALL include unit tests for the link validation module with mocked HTTP responses.

#### Scenario: Accessible 200 response with body

- **WHEN** `tests/test_link_validator.py` runs with a mocked 200 response and body exceeding the minimum byte threshold
- **THEN** the job match is marked `accessible`

#### Scenario: Inaccessible 404 response

- **WHEN** the test runs with a mocked 404 response
- **THEN** the job match is marked `inaccessible`

#### Scenario: Timeout handled

- **WHEN** the test runs with a mocked timeout
- **THEN** the job match is marked `inaccessible` and analysis does not raise

#### Scenario: Redirect followed

- **WHEN** the test runs with a mocked 302 redirect to a 200 destination with sufficient body
- **THEN** the job match is marked `accessible`

#### Scenario: 403 treated as unknown

- **WHEN** the test runs with a mocked 403 response
- **THEN** the job match is marked `unknown`

#### Scenario: Small body treated as inaccessible

- **WHEN** the test runs with a mocked 200 response and body below the minimum byte threshold
- **THEN** the job match is marked `inaccessible`

#### Scenario: Display filter excludes inaccessible

- **WHEN** the test runs `filter_displayable_matches()` on a mix of accessible, inaccessible, and unknown matches
- **THEN** inaccessible matches are excluded and accessible/unknown matches are retained

### Requirement: Report output reflects link filtering tests

The system SHALL verify link status and filtering appear in generated reports.

#### Scenario: CSV includes link_status column and excludes inaccessible

- **WHEN** report CSV tests run after validation with mixed link statuses
- **THEN** they assert `link_status` and `link_status_code` columns are present and inaccessible rows are omitted

#### Scenario: Integration test mocks link validation

- **WHEN** `tests/test_integration_pipeline.py` runs
- **THEN** link validation HTTP GET calls are mocked and results include link status fields with inaccessible jobs filtered from outputs

### Requirement: Test suite runs without external services

The system SHALL include a pytest suite that validates all capabilities without requiring live calls to external job APIs, Ollama, or job listing URLs.

#### Scenario: All externals mocked

- **WHEN** `pytest` runs
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, Ollama, or job listing URLs

#### Scenario: WeasyPrint mocked in default test run

- **WHEN** `pytest` runs in CI or environments without WeasyPrint system libraries
- **THEN** PDF rendering tests mock WeasyPrint and still pass

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

#### Scenario: Integration writes canonical Markdown

- **WHEN** `tests/test_integration_pipeline.py` runs POST /analyze with mocked externals
- **THEN** it verifies `reports/market_fit_report.md` exists

#### Scenario: Integration writes PDF when renderer succeeds

- **WHEN** integration test mocks WeasyPrint successfully
- **THEN** it verifies `reports/market_fit_report.pdf` exists

### Requirement: Canonical Markdown report tests

The system SHALL include tests that validate the structure and content of the canonical `market_fit_report.md` builder.

#### Scenario: All required sections present

- **WHEN** `tests/test_report_markdown.py` runs against `build_report_markdown()`
- **THEN** it verifies title, date, executive summary, market overview tables, top missing skills, per-source snapshot table, top 20 jobs table, study recommendation, and attribution are present

#### Scenario: No raw job descriptions in Markdown

- **WHEN** the Markdown builder runs with fixture data containing job descriptions
- **THEN** the output does not contain raw job description text

#### Scenario: Top 20 jobs rendered as table

- **WHEN** the Markdown builder runs with more than 20 matching jobs
- **THEN** the top jobs section contains a GFM table with at most 20 data rows sorted by fit score

### Requirement: Markdown-first PDF rendering tests

The system SHALL include tests for the WeasyPrint PDF rendering path.

#### Scenario: PDF render called with HTML containing report sections

- **WHEN** `tests/test_report_pdf.py` runs with WeasyPrint mocked
- **THEN** it verifies the render pipeline is invoked with HTML containing headings and table elements derived from the canonical Markdown

#### Scenario: PDF skipped gracefully when WeasyPrint fails

- **WHEN** the PDF renderer raises an import or runtime error
- **THEN** tests verify Markdown is still written, PDF is skipped, and a warning is returned

#### Scenario: Multiple job rows do not break PDF pipeline

- **WHEN** PDF generation runs with 5+ top matching jobs in fixture data
- **THEN** the render pipeline completes without error (regression for consecutive-row layout failures)

### Requirement: Test fixtures and configuration

The system SHALL provide shared test fixtures and pytest configuration.

#### Scenario: Shared fixtures available

- **WHEN** any test module runs
- **THEN** `tests/conftest.py` provides fixtures including a sample PDF, API response JSON payloads, and isolated temporary data/report directories

#### Scenario: Pytest configuration documented

- **WHEN** a developer reads the README
- **THEN** it documents how to run the test suite with `pytest`
