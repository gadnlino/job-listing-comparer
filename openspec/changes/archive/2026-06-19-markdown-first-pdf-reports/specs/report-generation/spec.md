## MODIFIED Requirements

### Requirement: Market summary Markdown report

The system SHALL generate `reports/market_fit_report.md` after each analysis run as the single canonical report document. This file is the source of truth for both Markdown download and PDF rendering. It SHALL contain: title and generated date, executive summary, total jobs analyzed, jobs by source (as a table), jobs by career track (as a table), skills detected in resume, top 20 most requested skills, top 20 missing skills, per-source snapshot (as a table), top 20 jobs with highest fit score (as a table), and a deterministic study recommendation.

#### Scenario: Canonical Markdown report generated after analysis

- **WHEN** analysis completes
- **THEN** the system writes `reports/market_fit_report.md` with all required sections in print-ready Markdown format including GFM tables where specified

#### Scenario: Markdown is PDF source of truth

- **WHEN** the PDF report is generated
- **THEN** it is rendered from the same `market_fit_report.md` content written in the same analysis run — not from a separate parallel builder

#### Scenario: Deterministic study recommendation

- **WHEN** the market summary is generated
- **THEN** the study recommendation is computed deterministically based on demand by track, average fit score by track, missing skills frequency, and number of high-fit jobs per track

#### Scenario: High demand and high fit track marked as near-term opportunity

- **WHEN** a career track has high demand and high average fit score
- **THEN** the recommendation marks it as a strong near-term opportunity

#### Scenario: High demand medium fit track marked as specialization candidate

- **WHEN** a career track has high demand but medium fit score
- **THEN** the recommendation marks it as a good specialization candidate

#### Scenario: Repeated missing skills recommended for study

- **WHEN** missing skills appear frequently across many high-fit jobs
- **THEN** the recommendation lists those skills as priority study targets

### Requirement: Report download endpoints

The system SHALL provide download endpoints for generated reports.

#### Scenario: CSV download available

- **WHEN** the user requests `GET /download/job_matches.csv` and the file exists
- **THEN** the system returns the CSV file as a download

#### Scenario: Markdown download available

- **WHEN** the user requests `GET /download/market_summary.md` and the canonical report file exists
- **THEN** the system returns `reports/market_fit_report.md` as a Markdown download

#### Scenario: Download endpoint friendly error when file missing

- **WHEN** the user requests a download endpoint and the report file does not exist
- **THEN** the system returns a friendly error message indicating the file is not available

### Requirement: Local report storage

The system SHALL store generated reports locally as CSV, Markdown, and PDF files without using a database.

#### Scenario: Reports overwritten on new analysis

- **WHEN** a new analysis is run
- **THEN** previous reports in `reports/` are overwritten with the new results

### Requirement: Local LLM executive summary

The system SHALL use a local Ollama instance via HTTP to generate a narrative executive summary for the report from the structured `ReportSummaryContext` only.

#### Scenario: Ollama generates executive summary

- **WHEN** Ollama is reachable at the configured base URL and analysis completes with at least one job
- **THEN** the system sends the structured context to Ollama and receives a 2–3 paragraph executive summary for inclusion in the canonical Markdown report and PDF

#### Scenario: Ollama unavailable fallback

- **WHEN** Ollama is unreachable or returns an error
- **THEN** the system generates a deterministic template executive summary from the same structured context and still produces the Markdown report and PDF (when WeasyPrint is available)

#### Scenario: LLM does not alter deterministic sections

- **WHEN** the report is generated
- **THEN** tables, skill lists, top jobs, and study recommendation are rendered deterministically from computed data — only the executive summary narrative section uses LLM output

### Requirement: Summary PDF report

The system SHALL generate `reports/market_fit_report.pdf` after each analysis run by rendering the canonical `market_fit_report.md` through Markdown → HTML → WeasyPrint. The PDF SHALL be a reliably formatted view of the same content as the Markdown report.

#### Scenario: PDF generated after analysis

- **WHEN** analysis completes with at least one job match and WeasyPrint is available
- **THEN** the system writes `reports/market_fit_report.pdf` rendered from `market_fit_report.md`

#### Scenario: PDF sections included

- **WHEN** the summary PDF is generated
- **THEN** it includes: title and date, executive summary (LLM or template fallback), resume skills, market overview tables, top missing skills, per-source snapshot table, top 20 matching jobs table, deterministic study recommendation, and job source attribution (including Remotive credit where applicable)

#### Scenario: PDF uses formatted tables

- **WHEN** the summary PDF is generated
- **THEN** market overview, per-source snapshot, and top 20 jobs sections render as formatted HTML tables (not plain concatenated text lines)

#### Scenario: PDF is summary only

- **WHEN** the summary PDF is generated
- **THEN** it does NOT include the full job table — full data remains in `job_matches.csv`

#### Scenario: PDF not generated when no jobs found

- **WHEN** analysis completes with zero job matches
- **THEN** the system does not generate the PDF and shows a friendly message on the results page

#### Scenario: PDF skipped when WeasyPrint unavailable

- **WHEN** analysis completes with job matches but WeasyPrint cannot render (missing import or system libraries)
- **THEN** the system still writes `market_fit_report.md`, skips PDF generation, sets `pdf_generated=False`, and adds a warning explaining how to install WeasyPrint dependencies

## ADDED Requirements

### Requirement: Markdown-first PDF rendering pipeline

The system SHALL render PDF reports using a Markdown-first pipeline: build canonical Markdown, convert to HTML with a CSS stylesheet via WeasyPrint, and write the PDF output. The system SHALL NOT use fpdf2 for report generation.

#### Scenario: Pipeline steps executed in order

- **WHEN** report generation runs with at least one job match
- **THEN** the system first writes `market_fit_report.md`, then converts that Markdown to HTML wrapped in a report template with `report.css`, then renders PDF via WeasyPrint

#### Scenario: CSS controls PDF layout

- **WHEN** the PDF is rendered
- **THEN** typography, heading hierarchy, table borders, page margins, and URL wrapping are controlled by `src/analysis/templates/report.css`

## REMOVED Requirements

### Requirement: Direct fpdf2 PDF layout

**Reason:** Imperative fpdf2 layout duplicated Markdown content, produced unreliable formatting, and could not consistently render spec-required tables.

**Migration:** PDF is rendered from canonical Markdown via WeasyPrint. Remove `write_summary_pdf()` and `fpdf2` dependency.
