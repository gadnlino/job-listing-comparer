# Report Generation

Generates CSV, Markdown, and PDF reports after job matching and link validation.

## Requirements

### Requirement: Job listing URL validation

The system SHALL validate the reachability of each job listing URL after job matching completes and before report generation begins, using HTTP GET requests only.

#### Scenario: Accessible URL marked accessible

- **WHEN** a job match has a non-empty URL and an HTTP GET request completes with a 2xx response after redirects and a body exceeding the minimum byte threshold
- **THEN** the job match `link_status` is set to `accessible`

#### Scenario: Inaccessible URL marked inaccessible

- **WHEN** a job match URL returns 404, 410, 5xx, times out, raises a connection error, is empty, or returns 2xx with insufficient body content
- **THEN** the job match `link_status` is set to `inaccessible`

#### Scenario: Ambiguous blocking marked unknown

- **WHEN** a job match URL returns HTTP 403 or 429
- **THEN** the job match `link_status` is set to `unknown`

#### Scenario: Redirect chains followed

- **WHEN** a job listing URL redirects (e.g. Adzuna `redirect_url`) and the final destination responds successfully with sufficient body content
- **THEN** the link is marked `accessible`

#### Scenario: Inaccessible jobs excluded from user-facing outputs

- **WHEN** link validation runs and one or more jobs are marked `inaccessible`
- **THEN** those jobs are excluded from the results table, CSV export, and report top-jobs tables

#### Scenario: Market stats use full match set

- **WHEN** link validation runs and jobs are marked `inaccessible`
- **THEN** market overview statistics and LLM summary input still include all matched jobs regardless of link status

#### Scenario: Validation failure isolation

- **WHEN** an unexpected error occurs while checking a single URL
- **THEN** that job is marked `unknown` and analysis continues for remaining jobs

#### Scenario: Validation can be disabled

- **WHEN** `LINK_VALIDATION_ENABLED=false` in environment configuration
- **THEN** the system skips HTTP checks, sets all link statuses to `unknown`, and does not filter any jobs from outputs

#### Scenario: Validation bounded by timeout and concurrency

- **WHEN** link validation runs on N job matches
- **THEN** each GET request respects configured timeout and concurrency limits to avoid blocking analysis indefinitely

### Requirement: Job matches CSV report

The system SHALL generate `reports/job_matches.csv` after each analysis run with columns: source, title, company, location, country, remote_type, url, primary_track, fit_score, matched_skills, missing_skills, salary_min, salary_max, currency, seniority_estimate, link_status, link_status_code. The CSV SHALL include only jobs with `accessible` or `unknown` link status.

#### Scenario: CSV generated after analysis

- **WHEN** analysis completes with one or more job matches
- **THEN** the system writes `reports/job_matches.csv` with one row per displayable job match (accessible or unknown) including link validation columns

#### Scenario: Inaccessible jobs omitted from CSV

- **WHEN** analysis completes and some job matches are marked `inaccessible`
- **THEN** those jobs are not included as rows in the CSV

#### Scenario: CSV sorted by fit score

- **WHEN** the CSV report is generated
- **THEN** rows are sorted by fit_score descending

### Requirement: Summary PDF report

The system SHALL generate `reports/market_fit_report.pdf` after each analysis run by rendering the canonical `market_fit_report.md` through Markdown → HTML → WeasyPrint. The PDF SHALL be a reliably formatted view of the same content as the Markdown report.

#### Scenario: PDF sections included

- **WHEN** the summary PDF is generated
- **THEN** it includes: title and date, executive summary (LLM or template fallback), resume skills, market overview tables, top missing skills, per-source snapshot table, top 20 matching jobs table (accessible and unknown only, with link status column for unknown entries), deterministic study recommendation, and job source attribution (including Remotive credit where applicable)

#### Scenario: PDF generated after analysis

- **WHEN** analysis completes with at least one job match and WeasyPrint is available
- **THEN** the system writes `reports/market_fit_report.pdf` rendered from `market_fit_report.md`

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

### Requirement: Market summary Markdown report

The system SHALL generate `reports/market_fit_report.md` after each analysis run as the single canonical report document. This file is the source of truth for both Markdown download and PDF rendering. It SHALL contain: title and generated date, executive summary, total jobs analyzed, jobs by source (as a table), jobs by career track (as a table), skills detected in resume, top 20 most requested skills, top 20 missing skills, per-source snapshot (as a table), top 20 jobs with highest fit score (as a table from accessible and unknown matches only, including link status for unknown entries), and a deterministic study recommendation.

#### Scenario: Excluded link summary in report

- **WHEN** one or more job links are marked inaccessible and excluded from output
- **THEN** the Markdown report includes a note with the count of excluded (inaccessible) links per source

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

#### Scenario: Canonical Markdown report generated after analysis

- **WHEN** analysis completes
- **THEN** the system writes `reports/market_fit_report.md` with all required sections in print-ready Markdown format including GFM tables where specified

#### Scenario: Markdown is PDF source of truth

- **WHEN** the PDF report is generated
- **THEN** it is rendered from the same `market_fit_report.md` content written in the same analysis run — not from a separate parallel builder

### Requirement: Results page job table

The system SHALL display a sortable table of analyzed job matches on the results page, including only jobs with accessible or unknown link status.

#### Scenario: Job table columns

- **WHEN** the results page renders with matches
- **THEN** each row shows title, company, location, source, primary track, fit score, matched skills, missing skills, and a link action (clickable "View" when accessible; neutral indicator when unknown)

#### Scenario: Link validation exclusion warning displayed

- **WHEN** more than 20% of validated links for a source are inaccessible
- **THEN** the results page displays a warning summarizing how many links were excluded for that source

### Requirement: Link validation summary statistics

The system SHALL compute per-source counts of accessible, inaccessible, unknown, and excluded links after validation completes.

#### Scenario: Per-source excluded count

- **WHEN** validation completes
- **THEN** the system can report how many links were inaccessible (excluded) per source for warnings and report footnotes

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

### Requirement: Structured report context for LLM

The system SHALL build a `ReportSummaryContext` structured object from computed analysis results before any LLM call. This object MUST contain only aggregated metrics and metadata — never raw job descriptions or resume text.

#### Scenario: Context includes computed aggregates

- **WHEN** report generation prepares data for the LLM
- **THEN** the context includes resume skills, total jobs analyzed, jobs by source, jobs by track, top requested skills, top missing skills, per-source summary stats, pre-computed study recommendation, and top matching jobs metadata

#### Scenario: Top matching jobs filtered by fit

- **WHEN** the system selects jobs for the LLM context and PDF highlights
- **THEN** only the top 20 jobs by fit score are included

#### Scenario: Job metadata excludes descriptions

- **WHEN** a job is included in the LLM context or PDF top-jobs table
- **THEN** the entry includes title, company, source, fit_score, primary_track, matched_skills, missing_skills, seniority_estimate, and url only — never the job description field

#### Scenario: Raw text never sent to LLM

- **WHEN** the system calls the LLM for executive summary generation
- **THEN** the prompt contains only the serialized `ReportSummaryContext` JSON and MUST NOT include raw resume text or raw job descriptions

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

### Requirement: PDF report download endpoint

The system SHALL provide a download endpoint for the summary PDF report.

#### Scenario: PDF download available

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file exists
- **THEN** the system returns the PDF file with `Content-Type: application/pdf` and `Content-Disposition: inline` so the browser displays it in a new tab

#### Scenario: PDF download friendly error when missing

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file does not exist
- **THEN** the system returns a friendly error message indicating the file is not available

### Requirement: Markdown-first PDF rendering pipeline

The system SHALL render PDF reports using a Markdown-first pipeline: build canonical Markdown, convert to HTML with a CSS stylesheet via WeasyPrint, and write the PDF output. The system SHALL NOT use fpdf2 for report generation.

#### Scenario: Pipeline steps executed in order

- **WHEN** report generation runs with at least one job match
- **THEN** the system first writes `market_fit_report.md`, then converts that Markdown to HTML wrapped in a report template with `report.css`, then renders PDF via WeasyPrint

#### Scenario: CSS controls PDF layout

- **WHEN** the PDF is rendered
- **THEN** typography, heading hierarchy, table borders, page margins, and URL wrapping are controlled by `src/analysis/templates/report.css`
