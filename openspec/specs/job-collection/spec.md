# Job Collection

Collects and normalizes job postings from Remotive, Adzuna, and Arbeitnow.

## Requirements

### Requirement: Base collector interface

The system SHALL define a base collector interface with a `search_jobs(query, max_results, **kwargs) -> list[JobPosting]` method that all job source collectors implement.

#### Scenario: Collector returns normalized JobPosting objects

- **WHEN** any collector successfully fetches jobs
- **THEN** each result is a normalized `JobPosting` object with the original API response stored in `raw_payload`

#### Scenario: Collector handles API errors gracefully

- **WHEN** a collector encounters an API error or network failure
- **THEN** the collector returns an empty list and a warning message without crashing the application

### Requirement: Remotive job collector

The system SHALL collect remote/global tech jobs from the Remotive public API at `https://remotive.com/api/remote-jobs` without requiring an API key or authentication.

#### Scenario: Successful Remotive search

- **WHEN** the Remotive collector is invoked
- **THEN** the system returns normalized `JobPosting` objects from the Remotive API response

#### Scenario: Remotive as guaranteed fallback source

- **WHEN** no API credentials are configured for any source
- **THEN** the Remotive collector still functions and returns job results

#### Scenario: Remotive batch fetch respects rate limits

- **WHEN** the Remotive collector runs during an analysis
- **THEN** the system makes at most one API call to Remotive per analysis run, fetching jobs in batch (e.g. `category=software-dev`) and filtering client-side against default query keywords

#### Scenario: Remotive attribution

- **WHEN** Remotive jobs are displayed in the UI or reports
- **THEN** the system attributes Remotive as the source and links to Remotive job URLs

#### Scenario: Remotive jobs delayed 24 hours

- **WHEN** Remotive jobs are collected
- **THEN** the system accepts that the public API provides listings delayed by up to 24 hours per Remotive terms

### Requirement: Adzuna job collector with optional credentials

The system SHALL collect jobs from the Adzuna Job Search API at `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}` when `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` environment variables are configured. Both credentials MUST be passed as query parameters (`app_id`, `app_key`) on every request.

#### Scenario: Adzuna search with credentials

- **WHEN** Adzuna credentials are present and the collector is invoked with query, country, page, and results_per_page
- **THEN** the system returns normalized `JobPosting` objects from the Adzuna API

#### Scenario: Adzuna skipped without credentials

- **WHEN** `ADZUNA_APP_ID` or `ADZUNA_APP_KEY` is missing or empty
- **THEN** the system skips Adzuna collection and displays a friendly warning without crashing

#### Scenario: Adzuna credentials obtained via developer registration

- **WHEN** a user wants to enable Adzuna
- **THEN** they register at the Adzuna Developer Portal (developer.adzuna.com), create an application, and add the App ID and App Key to `.env`

#### Scenario: Adzuna country selection

- **WHEN** the user selects an Adzuna country (gb, us, es, de, nl, ie)
- **THEN** the Adzuna collector searches jobs in that country

#### Scenario: Default Adzuna countries

- **WHEN** Adzuna is selected with "All" countries and credentials are configured
- **THEN** the system searches across gb, us, es, de, nl, and ie

### Requirement: Arbeitnow job collector

The system SHALL collect European job market data from the Arbeitnow public API at `https://www.arbeitnow.com/api/job-board-api` without scraping, authentication, or an API key.

#### Scenario: Successful Arbeitnow search

- **WHEN** the Arbeitnow collector is invoked
- **THEN** the system returns normalized `JobPosting` objects from the Arbeitnow API

#### Scenario: Arbeitnow paginated fetch with client-side filtering

- **WHEN** the Arbeitnow collector runs during an analysis with multiple default queries
- **THEN** the system fetches paginated results and filters client-side against query keywords rather than making one API call per query

#### Scenario: Incomplete Arbeitnow fields handled gracefully

- **WHEN** an Arbeitnow job posting has missing salary, country, or other optional fields
- **THEN** the system normalizes the job with nullable fields set to None without error

### Requirement: Zero-configuration minimum setup

The system SHALL function with no API keys configured, using Remotive and Arbeitnow as the guaranteed data sources.

#### Scenario: App runs without any credentials

- **WHEN** no environment variables for job API credentials are set
- **THEN** the system collects jobs from Remotive and Arbeitnow and skips Adzuna with a warning

### Requirement: Multi-source fault tolerance

The system SHALL continue collecting jobs from remaining sources when one source fails.

#### Scenario: One source fails, others succeed

- **WHEN** one job API source returns an error during collection
- **THEN** the system collects jobs from the other selected sources and displays a warning for the failed source

#### Scenario: Source selector

- **WHEN** the user selects a source (Remotive, Adzuna, Arbeitnow, or All) on the upload form
- **THEN** the system collects jobs only from the selected source(s)

### Requirement: Default search queries

The system SHALL run predefined default search queries when analyzing a resume, including at minimum: backend engineer aws, python aws engineer, serverless engineer, api integration engineer, platform engineer, site reliability engineer, cloud security engineer, aws security engineer, devsecops engineer, llm engineer, ai engineer rag, genai engineer, data engineer aws.

#### Scenario: Default queries executed on analyze

- **WHEN** the user submits a resume for analysis
- **THEN** the system applies the predefined default queries to filter and match collected jobs; Remotive and Arbeitnow use client-side filtering after batch fetch, Adzuna uses per-query API calls when credentials are configured

### Requirement: JobPosting data model

The system SHALL normalize all collected jobs into a `JobPosting` Pydantic model with fields: id, source, title, company, location, country, remote_type, url, description, salary_min, salary_max, currency, created_at, raw_payload.

#### Scenario: All sources produce common format

- **WHEN** jobs are collected from Remotive, Adzuna, and Arbeitnow
- **THEN** all jobs are represented as `JobPosting` objects with the same field schema
