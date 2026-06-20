## MODIFIED Requirements

### Requirement: Test suite runs without external services

The system SHALL include a pytest suite that validates all capabilities without requiring live calls to external job APIs or Ollama.

#### Scenario: All externals mocked

- **WHEN** `pytest` runs
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, or Ollama

#### Scenario: WeasyPrint mocked in default test run

- **WHEN** `pytest` runs in CI or environments without WeasyPrint system libraries
- **THEN** PDF rendering tests mock WeasyPrint and still pass

## ADDED Requirements

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
- **THEN** it verifies `write_pdf` is invoked with HTML containing headings and table elements derived from the canonical Markdown

#### Scenario: PDF skipped gracefully when WeasyPrint fails

- **WHEN** the PDF renderer raises an import or runtime error
- **THEN** tests verify Markdown is still written, PDF is skipped, and a warning is returned

#### Scenario: Multiple job rows do not break PDF pipeline

- **WHEN** PDF generation runs with 5+ top matching jobs in fixture data
- **THEN** the render pipeline completes without error (regression for consecutive-row layout failures)

### Requirement: Integration pipeline tests updated

The system SHALL update integration tests to reflect the Markdown-first report pipeline.

#### Scenario: Integration writes canonical Markdown

- **WHEN** `tests/test_integration_pipeline.py` runs POST /analyze with mocked externals
- **THEN** it verifies `reports/market_fit_report.md` exists (replacing `market_summary.md` assertion)

#### Scenario: Integration writes PDF when renderer succeeds

- **WHEN** integration test mocks WeasyPrint successfully
- **THEN** it verifies `reports/market_fit_report.pdf` exists

## REMOVED Requirements

### Requirement: fpdf2 PDF layout tests

**Reason:** fpdf2 direct layout removed; PDF tests now cover Markdown-first WeasyPrint pipeline.

**Migration:** Replace `write_summary_pdf` fpdf2 tests with `build_report_markdown` + mocked WeasyPrint render tests.
