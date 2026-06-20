## MODIFIED Requirements

### Requirement: Test suite runs without external services

The system SHALL include a pytest suite that validates all capabilities without requiring live calls to external job APIs, LLM providers (including Groq), Ollama, job listing URLs, or browser PDF libraries at runtime in CI.

#### Scenario: All externals mocked

- **WHEN** `pytest` runs
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, Groq, Ollama, or job listing URLs

#### Scenario: WeasyPrint mocked in default test run

- **WHEN** `pytest` runs in CI or environments without WeasyPrint system libraries
- **THEN** PDF rendering tests mock WeasyPrint and still pass

#### Scenario: Browser PDF mode does not require WeasyPrint in CI

- **WHEN** tests run with `PDF_RENDERER=browser`
- **THEN** report generation tests pass without WeasyPrint installed or invoked on the server

## MODIFIED Requirements

### Requirement: Comprehensive pytest test suite

The system SHALL include a pytest test suite covering all capabilities: resume parsing, job collection, job matching, report generation, and web application. Every spec scenario MUST have a corresponding test case.

#### Scenario: Test suite runs offline

- **WHEN** the developer runs `pytest`
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, Groq, or Ollama

#### Scenario: External HTTP mocked in tests

- **WHEN** tests exercise job collectors or the LLM summarizer
- **THEN** all external HTTP requests are mocked using fixture JSON payloads

## MODIFIED Requirements

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
- **THEN** it verifies the prompt contains only structured JSON, never raw job descriptions, OpenAI-compatible chat completion requests include Authorization when `LLM_API_KEY` is set, and template fallback works when all LLM providers fail

#### Scenario: HTML report builder tests

- **WHEN** report HTML builder tests run
- **THEN** they verify Markdown is converted to HTML containing required section headings and table markup for both WeasyPrint and browser paths

#### Scenario: Server PDF tests in weasyprint mode

- **WHEN** `tests/test_report_pdf.py` runs with `PDF_RENDERER=weasyprint`
- **THEN** it verifies PDF file creation with required sections (WeasyPrint mocked) and skips generation when no jobs are found

#### Scenario: Browser PDF mode skips server PDF write

- **WHEN** report generation tests run with `PDF_RENDERER=browser`
- **THEN** they verify `market_fit_report.md` is written, no server `.pdf` is required, and `pdf_generated` is true when jobs exist

## MODIFIED Requirements

### Requirement: Web application tests

The system SHALL include tests for all HTTP routes and UI warnings covering all web-app spec scenarios.

#### Scenario: Print route returns HTML when report exists

- **WHEN** `GET /report/print` is requested after a successful analysis with `PDF_RENDERER=browser`
- **THEN** the response is HTML containing report content and client-side auto-download script markup

#### Scenario: Auto-open script targets print route in browser mode

- **WHEN** web app tests render the results page with `PDF_RENDERER=browser` and `pdf_generated=True`
- **THEN** the page includes script opening `/report/print` in a new tab
