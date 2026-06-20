## ADDED Requirements

### Requirement: Job matches CSV report

The system SHALL generate `reports/job_matches.csv` after each analysis run with columns: source, title, company, location, country, remote_type, url, primary_track, fit_score, matched_skills, missing_skills, salary_min, salary_max, currency, seniority_estimate.

#### Scenario: CSV generated after analysis

- **WHEN** analysis completes with one or more job matches
- **THEN** the system writes `reports/job_matches.csv` with one row per job match

#### Scenario: CSV sorted by fit score

- **WHEN** the CSV report is generated
- **THEN** rows are sorted by fit_score descending

### Requirement: Market summary Markdown report

The system SHALL generate `reports/market_summary.md` after each analysis run containing: executive summary, total jobs analyzed, jobs by source, jobs by career track, skills detected in resume, top 20 most requested skills, top 20 missing skills, top 20 jobs with highest fit score, career tracks with highest demand, career tracks where fit is highest, career tracks with biggest skill gaps, and a deterministic study recommendation.

#### Scenario: Markdown report generated after analysis

- **WHEN** analysis completes
- **THEN** the system writes `reports/market_summary.md` with all required sections

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

- **WHEN** the user requests `GET /download/market_summary.md` and the file exists
- **THEN** the system returns the Markdown file as a download

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

The system SHALL use a local Ollama instance via HTTP to generate a narrative executive summary for the PDF report from the structured `ReportSummaryContext` only.

#### Scenario: Ollama generates executive summary

- **WHEN** Ollama is reachable at the configured base URL and analysis completes with at least one job
- **THEN** the system sends the structured context to Ollama and receives a 2–3 paragraph executive summary for inclusion in the PDF

#### Scenario: Ollama unavailable fallback

- **WHEN** Ollama is unreachable or returns an error
- **THEN** the system generates a deterministic template executive summary from the same structured context and still produces the PDF

#### Scenario: LLM does not alter deterministic sections

- **WHEN** the PDF report is generated
- **THEN** tables, skill lists, top jobs, and study recommendation are rendered deterministically from computed data — only the executive summary narrative section uses LLM output

### Requirement: Summary PDF report

The system SHALL generate `reports/market_fit_report.pdf` after each analysis run as a single consolidated summary document containing the most important results from all platforms.

#### Scenario: PDF generated after analysis

- **WHEN** analysis completes with at least one job match
- **THEN** the system writes `reports/market_fit_report.pdf`

#### Scenario: PDF sections included

- **WHEN** the summary PDF is generated
- **THEN** it includes: title and date, executive summary (LLM or template fallback), resume skills, market overview, top missing skills, per-source snapshot, top 20 matching jobs table, deterministic study recommendation, and job source attribution (including Remotive credit where applicable)

#### Scenario: PDF is summary only

- **WHEN** the summary PDF is generated
- **THEN** it does NOT include the full job table — full data remains in `job_matches.csv`

#### Scenario: PDF not generated when no jobs found

- **WHEN** analysis completes with zero job matches
- **THEN** the system does not generate the PDF and shows a friendly message on the results page

### Requirement: PDF report download endpoint

The system SHALL provide a download endpoint for the summary PDF report.

#### Scenario: PDF download available

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file exists
- **THEN** the system returns the PDF file with `Content-Type: application/pdf` and `Content-Disposition: inline` so the browser displays it in a new tab

#### Scenario: PDF download friendly error when missing

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file does not exist
- **THEN** the system returns a friendly error message indicating the file is not available
