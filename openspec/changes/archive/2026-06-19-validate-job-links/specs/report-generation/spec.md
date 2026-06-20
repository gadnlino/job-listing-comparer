## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Market summary Markdown report

The system SHALL generate `reports/market_fit_report.md` after each analysis run as the single canonical report document. This file is the source of truth for both Markdown download and PDF rendering. It SHALL contain: title and generated date, executive summary, total jobs analyzed, jobs by source (as a table), jobs by career track (as a table), skills detected in resume, top 20 most requested skills, top 20 missing skills, per-source snapshot (as a table), top 20 jobs with highest fit score (as a table from accessible and unknown matches only, including link status for unknown entries), and a deterministic study recommendation.

#### Scenario: Excluded link summary in report

- **WHEN** one or more job links are marked inaccessible and excluded from output
- **THEN** the Markdown report includes a note with the count of excluded (inaccessible) links per source

### Requirement: Results page job table

The system SHALL display a sortable table of analyzed job matches on the results page, including only jobs with accessible or unknown link status.

#### Scenario: Job table columns

- **WHEN** the results page renders with matches
- **THEN** each row shows title, company, location, source, primary track, fit score, matched skills, missing skills, and a link action (clickable "View" when accessible; neutral indicator when unknown)

#### Scenario: Link validation exclusion warning displayed

- **WHEN** more than 20% of validated links for a source are inaccessible
- **THEN** the results page displays a warning summarizing how many links were excluded for that source

## ADDED Requirements

### Requirement: Link validation summary statistics

The system SHALL compute per-source counts of accessible, inaccessible, unknown, and excluded links after validation completes.

#### Scenario: Per-source excluded count

- **WHEN** validation completes
- **THEN** the system can report how many links were inaccessible (excluded) per source for warnings and report footnotes
