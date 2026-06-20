## ADDED Requirements

### Requirement: Local HTTP server

The system SHALL run as a local web application served by Uvicorn with FastAPI, accessible at `http://localhost:8000`.

#### Scenario: Server starts with reload

- **WHEN** the user runs `uvicorn src.app:app --reload`
- **THEN** the application starts and serves HTTP requests locally

### Requirement: Home page with upload form

The system SHALL serve a home page at `GET /` with a resume upload form and analysis controls.

#### Scenario: Upload form displayed

- **WHEN** the user navigates to `/`
- **THEN** the page shows the app title, a short explanation, a PDF upload field, an optional max results field (default 100), a source selector (Remotive, Adzuna, Arbeitnow, All), an optional Adzuna country selector (gb, us, es, de, nl, ie), and an Analyze button

### Requirement: Analysis endpoint

The system SHALL provide `POST /analyze` that accepts a multipart form with the resume PDF and analysis options, performs the full analysis pipeline, and renders the results page.

#### Scenario: Successful analysis flow

- **WHEN** the user uploads a valid PDF and clicks Analyze
- **THEN** the system validates the PDF, extracts text, detects skills via `skills.json` catalog, collects jobs from selected sources, normalizes and classifies jobs, calculates fit scores, generates reports, and renders the results page

#### Scenario: Invalid PDF rejected at analyze

- **WHEN** the user submits a non-PDF file to `/analyze`
- **THEN** the system returns an error without crashing

### Requirement: Results page display

The system SHALL render a results page showing analysis outcomes after a successful `/analyze` request.

#### Scenario: Summary information displayed

- **WHEN** analysis completes with results
- **THEN** the results page shows total jobs analyzed, sources used, and any source failure warnings

#### Scenario: Skills and track breakdown displayed

- **WHEN** analysis completes
- **THEN** the results page shows detected resume skills (canonical names from `DetectedSkill`), number of jobs by career track, top 20 most requested skills, top 20 missing skills, and top 20 jobs with highest fit score

#### Scenario: Full job table sorted by fit score

- **WHEN** analysis completes with job matches
- **THEN** the results page displays a table sorted by fit score descending with columns: title, company, location, source, primary career track, fit score, matched skills, missing skills, and a link to the job posting opening in a new tab

#### Scenario: No jobs found message

- **WHEN** analysis completes but no jobs were collected from any source
- **THEN** the results page displays a clear message indicating no jobs were found

#### Scenario: API failure warnings displayed

- **WHEN** one or more job sources fail during collection
- **THEN** the results page displays warning messages for each failed source

#### Scenario: Adzuna skipped warning displayed

- **WHEN** Adzuna is selected but credentials are not configured
- **THEN** the results page displays a friendly warning that Adzuna was skipped and how to enable it

#### Scenario: Job source attribution displayed

- **WHEN** analysis completes with Remotive jobs in results
- **THEN** the results page attributes Remotive as a job source with a link to remotive.com

### Requirement: Minimal UI without frontend framework

The system SHALL use Jinja2 templates and plain HTML/CSS for the web interface without React, Vue, Angular, or any frontend framework.

#### Scenario: Templates rendered with Jinja2

- **WHEN** any page is served
- **THEN** the page is rendered from Jinja2 templates (`index.html`, `results.html`) with static CSS

### Requirement: Report download links on results page

The system SHALL display links on the results page to download generated CSV, Markdown, and PDF reports.

#### Scenario: Download links visible after analysis

- **WHEN** analysis completes and reports are generated
- **THEN** the results page shows links to download `job_matches.csv`, `market_summary.md`, and `market_fit_report.pdf`

#### Scenario: PDF link omitted when not generated

- **WHEN** analysis completes with zero job matches and no PDF was generated
- **THEN** the results page does not show a PDF download link

#### Scenario: LLM fallback warning displayed

- **WHEN** the PDF was generated using template fallback because Ollama was unavailable
- **THEN** the results page displays a friendly warning that the LLM summary was unavailable

### Requirement: Auto-open PDF report in new tab

The system SHALL attempt to open the summary PDF report in a new browser tab when analysis completes and the PDF was generated successfully. Implementation uses a small inline JavaScript snippet in `results.html` (no frontend framework).

#### Scenario: PDF auto-opens after successful analysis

- **WHEN** analysis completes and `market_fit_report.pdf` was generated
- **THEN** the results page includes an inline script that calls `window.open('/download/market_fit_report.pdf', '_blank')` on page load

#### Scenario: Popup blocked fallback displayed

- **WHEN** the browser blocks the automatic popup (`window.open` returns null)
- **THEN** the results page displays a prominent manual link or button to open the PDF report in a new tab

#### Scenario: No auto-open when PDF not generated

- **WHEN** analysis completes with zero job matches and no PDF was generated
- **THEN** the results page does not include the auto-open script

#### Scenario: Results page remains visible in current tab

- **WHEN** the PDF auto-open succeeds
- **THEN** the results page remains displayed in the current browser tab while the PDF opens in a separate tab
