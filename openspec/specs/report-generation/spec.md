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

The system SHALL produce a summary PDF view of the canonical `market_fit_report.md` using either server-side WeasyPrint (`PDF_RENDERER=weasyprint`) or client-side browser generation (`PDF_RENDERER=browser`). The PDF content SHALL match the Markdown report. When `PDF_RENDERER=off`, no PDF is produced.

#### Scenario: Server PDF via WeasyPrint

- **WHEN** `PDF_RENDERER=weasyprint`, analysis completes with at least one job match, and WeasyPrint is available
- **THEN** the system writes `reports/market_fit_report.pdf` rendered from `market_fit_report.md`

#### Scenario: Browser PDF without server file

- **WHEN** `PDF_RENDERER=browser` and analysis completes with at least one job match
- **THEN** the system writes `market_fit_report.md` and serves printable HTML at `GET /report/print` but does not require a server-side `.pdf` file

#### Scenario: PDF sections included

- **WHEN** a summary PDF is produced (server or browser path)
- **THEN** it includes: title and date, executive summary (LLM or template fallback), resume skills, market overview tables, top missing skills, per-source snapshot table, top 20 matching jobs table (accessible and unknown only), deterministic study recommendation, and job source attribution (including Remotive credit where applicable)

#### Scenario: PDF uses formatted tables

- **WHEN** the summary PDF is generated
- **THEN** market overview, per-source snapshot, and top 20 jobs sections render as formatted HTML tables (not plain concatenated text lines)

#### Scenario: PDF is summary only

- **WHEN** the summary PDF is generated
- **THEN** it does NOT include the full job table — full data remains in `job_matches.csv`

#### Scenario: PDF not generated when no jobs found

- **WHEN** analysis completes with zero job matches
- **THEN** the system does not offer PDF generation and shows a friendly message on the results page

#### Scenario: WeasyPrint unavailable in weasyprint mode

- **WHEN** `PDF_RENDERER=weasyprint`, job matches exist, but WeasyPrint cannot render
- **THEN** the system still writes `market_fit_report.md`, skips server PDF, sets `pdf_generated=False`, and adds a warning explaining how to install WeasyPrint dependencies

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

The system SHALL store generated reports locally as CSV and Markdown without using a database. A server-side PDF file SHALL be written only when `PDF_RENDERER=weasyprint` and rendering succeeds.

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

### Requirement: LLM executive summary

The system SHALL generate a narrative executive summary for the report from the structured `ReportSummaryContext` only, using an OpenAI-compatible HTTP chat completions API when configured, with Ollama and deterministic template fallbacks.

#### Scenario: OpenAI-compatible provider generates executive summary

- **WHEN** `LLM_BASE_URL` is configured, the provider is reachable, and analysis completes with at least one job
- **THEN** the system sends a chat completion request to `{LLM_BASE_URL}/v1/chat/completions` with the structured context in the user message and receives a 2–3 paragraph executive summary for inclusion in the canonical Markdown report and printable output

#### Scenario: API key sent for authenticated providers

- **WHEN** `LLM_API_KEY` is set and the system calls the OpenAI-compatible chat completions endpoint
- **THEN** the request includes an `Authorization: Bearer` header with the configured key

#### Scenario: Groq configured as cloud provider

- **WHEN** the user sets `LLM_BASE_URL` to `https://api.groq.com/openai/v1`, a valid `LLM_API_KEY`, and a supported `LLM_MODEL`
- **THEN** the system generates the executive summary via Groq without requiring a local llama.cpp or Ollama server

#### Scenario: Local llama.cpp without API key

- **WHEN** `LLM_BASE_URL` points to a local OpenAI-compatible server (e.g. llama.cpp) and `LLM_API_KEY` is unset
- **THEN** the system calls chat completions without an Authorization header and uses the response when successful

#### Scenario: Ollama fallback after OpenAI-compatible failure

- **WHEN** the OpenAI-compatible request fails or returns no usable content
- **THEN** the system attempts Ollama via `{OLLAMA_BASE_URL}/api/generate` before falling back to the template summary

#### Scenario: LLM unavailable fallback

- **WHEN** all configured LLM providers are unreachable or return errors
- **THEN** the system generates a deterministic template executive summary from the same structured context and still produces the Markdown report and printable output when jobs were matched

#### Scenario: LLM does not alter deterministic sections

- **WHEN** the report is generated
- **THEN** tables, skill lists, top jobs, and study recommendation are rendered deterministically from computed data — only the executive summary narrative section uses LLM output

### Requirement: Browser PDF auto-download

The system SHALL support client-side PDF generation in the user's browser when `PDF_RENDERER=browser`, automatically triggering a PDF download without requiring the user to click an in-app button.

#### Scenario: Printable HTML route available

- **WHEN** analysis completes with at least one job match and `PDF_RENDERER=browser`
- **THEN** the system serves `GET /report/print` as a print-ready HTML page built from the current `market_fit_report.md`

#### Scenario: Auto-download on print page load

- **WHEN** the printable HTML page loads in the browser after being opened from the post-analysis flow
- **THEN** client-side JavaScript automatically generates and downloads `market_fit_report.pdf` without an in-app "Save as PDF" button

#### Scenario: Markdown remains source of truth

- **WHEN** browser PDF mode is used
- **THEN** the downloadable PDF is derived from the same canonical Markdown content written in that analysis run

### Requirement: PDF report download endpoint

The system SHALL provide a download endpoint for the server-generated summary PDF when `PDF_RENDERER=weasyprint`.

#### Scenario: PDF download available in weasyprint mode

- **WHEN** the user requests `GET /download/market_fit_report.pdf`, `PDF_RENDERER=weasyprint`, and the file exists
- **THEN** the system returns the PDF file with `Content-Type: application/pdf` and `Content-Disposition: inline` so the browser displays it in a new tab

#### Scenario: PDF download friendly error when missing

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file does not exist
- **THEN** the system returns a friendly error message indicating the file is not available

#### Scenario: Browser mode uses print route instead

- **WHEN** `PDF_RENDERER=browser` and the user needs a PDF after analysis
- **THEN** the system directs the user to the auto-download printable route rather than a server `.pdf` file

### Requirement: Markdown-first PDF rendering pipeline

The system SHALL build printable report output using a Markdown-first pipeline: write canonical Markdown, convert to HTML with `report.css`, then render PDF via WeasyPrint when `PDF_RENDERER=weasyprint` or defer PDF rendering to the browser when `PDF_RENDERER=browser`. The system SHALL NOT use fpdf2 for report generation.

#### Scenario: Pipeline steps for server PDF mode

- **WHEN** report generation runs with at least one job match and `PDF_RENDERER=weasyprint`
- **THEN** the system first writes `market_fit_report.md`, then converts that Markdown to HTML wrapped in a report template with `report.css`, then renders PDF via WeasyPrint

#### Scenario: Pipeline steps for browser PDF mode

- **WHEN** report generation runs with at least one job match and `PDF_RENDERER=browser`
- **THEN** the system writes `market_fit_report.md` and makes the same Markdown → HTML conversion available via `GET /report/print` without invoking WeasyPrint on the server

#### Scenario: CSS controls report layout

- **WHEN** printable HTML is produced (for WeasyPrint or browser)
- **THEN** typography, heading hierarchy, table borders, page margins, and URL wrapping are controlled by `src/analysis/templates/report.css`
