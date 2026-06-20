# Web App

Local FastAPI web application for resume upload and analysis results.

## Requirements

### Requirement: Analysis loading indicator with live progress

The system SHALL display a loading indicator on the home page when the user submits the analyze form, update the status text from server progress events streamed during analysis, and navigate to the results page when analysis completes.

#### Scenario: Loading indicator shown on form submit

- **WHEN** the user clicks Analyze with a valid form and JavaScript is enabled
- **THEN** the loading indicator becomes visible immediately and the form submit is handled via `fetch` to the streaming endpoint

#### Scenario: Loading indicator updates from server progress

- **WHEN** the server emits a progress event during `/analyze/stream`
- **THEN** the loading status text updates to reflect the event `message` (including source and job title when provided)

#### Scenario: Validation counter displayed

- **WHEN** a progress event includes `current` and `total` during link validation
- **THEN** the loading indicator MAY display validation progress (e.g. 23/109)

#### Scenario: Form disabled during processing

- **WHEN** streaming analysis is in progress
- **THEN** the analyze submit button is disabled and the form cannot be submitted again

#### Scenario: Navigate to results on completion

- **WHEN** the client receives a `done` event with a `redirect` URL
- **THEN** the browser navigates to the results page

#### Scenario: Error displayed on stream failure

- **WHEN** the client receives an `error` event or the stream fails
- **THEN** the loading indicator is hidden, an error message is shown, and the form is re-enabled

#### Scenario: Graceful degradation without JavaScript

- **WHEN** JavaScript is disabled
- **THEN** the form submits via `POST /analyze` without the loading indicator or live progress

### Requirement: Local HTTP server

The system SHALL run as a local web application served by Uvicorn with FastAPI, accessible at `http://localhost:8000`.

#### Scenario: Server starts with reload

- **WHEN** the user runs `uvicorn src.app:app --reload`
- **THEN** the application starts and serves HTTP requests locally

### Requirement: Home page with upload form

The system SHALL serve a home page at `GET /` with a resume upload form and analysis controls.

#### Scenario: Upload form displayed

- **WHEN** the user navigates to `/`
- **THEN** the page shows the app title, a short explanation, a PDF upload field, an optional max results field (default 100), a source selector (Remotive, Adzuna, Arbeitnow, All), an optional Adzuna country selector (gb, us, es, de, nl, ie), an Analyze button, and a hidden loading indicator wired for streaming progress updates on submit

### Requirement: Analysis endpoint

The system SHALL provide analysis endpoints that accept a multipart form with the resume PDF and analysis options, perform the full analysis pipeline, and deliver results.

#### Scenario: Streaming analysis flow

- **WHEN** the client submits to `POST /analyze/stream` with a valid PDF
- **THEN** the system validates the PDF, runs the full pipeline, streams progress events, and completes with a redirect to the results page

#### Scenario: Successful analysis flow

- **WHEN** the user uploads a valid PDF and clicks Analyze
- **THEN** the system validates the PDF, extracts text, detects skills via `skills.json` catalog, collects jobs from selected sources, normalizes and classifies jobs, calculates fit scores, generates reports, and renders the results page

#### Scenario: Successful analysis flow (non-streaming fallback)

- **WHEN** the user uploads a valid PDF via `POST /analyze`
- **THEN** the system validates the PDF, extracts text, detects skills via `skills.json` catalog, collects jobs from selected sources, normalizes and classifies jobs, calculates fit scores, generates reports, and renders the results page

#### Scenario: Invalid PDF rejected at analyze

- **WHEN** the user submits a non-PDF file to an analyze endpoint
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

### Requirement: Results page link status display

The system SHALL reflect job listing link validation results on the analysis results page, showing only jobs with accessible or unknown link status.

#### Scenario: Inaccessible jobs excluded from table

- **WHEN** link validation marks one or more job matches as `inaccessible`
- **THEN** those jobs are not shown in the results table

#### Scenario: Accessible link is clickable

- **WHEN** a displayed job match has `link_status` of `accessible`
- **THEN** the results table shows a clickable link to the job URL

#### Scenario: Unknown link shown with neutral indicator

- **WHEN** a displayed job match has `link_status` of `unknown`
- **THEN** the results table shows the link with a neutral indicator that validation was inconclusive

#### Scenario: High exclusion rate warning

- **WHEN** more than 20% of validated links for a source are inaccessible
- **THEN** the results page includes a warning in the warnings section with source name, excluded count, and total validated count
