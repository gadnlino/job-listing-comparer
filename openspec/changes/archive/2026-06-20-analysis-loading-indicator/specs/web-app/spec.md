## ADDED Requirements

### Requirement: Analysis loading indicator with live progress

The system SHALL display a loading overlay on the home page when the user submits the analyze form, update the overlay text from server progress events streamed during analysis, and navigate to the results page when analysis completes.

#### Scenario: Overlay shown on form submit

- **WHEN** the user clicks Analyze with a valid form and JavaScript is enabled
- **THEN** a full-page loading overlay with spinner and status text becomes visible immediately and the form submit is handled via `fetch` to the streaming endpoint

#### Scenario: Overlay updates from server progress

- **WHEN** the server emits a progress event during `/analyze/stream`
- **THEN** the overlay status text updates to reflect the event `message` (including source and job title when provided)

#### Scenario: Validation counter displayed

- **WHEN** a progress event includes `current` and `total` during link validation
- **THEN** the overlay MAY display the validation progress (e.g. 23/109)

#### Scenario: Form disabled during processing

- **WHEN** streaming analysis is in progress
- **THEN** the analyze submit button is disabled and the form cannot be submitted again

#### Scenario: Navigate to results on completion

- **WHEN** the client receives a `done` event with a `redirect` URL
- **THEN** the browser navigates to the results page

#### Scenario: Error displayed on stream failure

- **WHEN** the client receives an `error` event or the stream fails
- **THEN** the overlay is hidden, an error message is shown, and the form is re-enabled

#### Scenario: Graceful degradation without JavaScript

- **WHEN** JavaScript is disabled
- **THEN** the form submits via `POST /analyze` without the overlay or live progress

## MODIFIED Requirements

### Requirement: Home page with upload form

The system SHALL serve a home page at `GET /` with a resume upload form and analysis controls.

#### Scenario: Upload form displayed

- **WHEN** the user navigates to `/`
- **THEN** the page shows the app title, a short explanation, a PDF upload field, an optional max results field (default 100), a source selector (Remotive, Adzuna, Arbeitnow, All), an optional Adzuna country selector (gb, us, es, de, nl, ie), an Analyze button, and a hidden loading overlay wired for streaming progress updates on submit

### Requirement: Analysis endpoint

The system SHALL provide analysis endpoints that accept a multipart form with the resume PDF and analysis options, perform the full analysis pipeline, and deliver results.

#### Scenario: Streaming analysis flow

- **WHEN** the client submits to `POST /analyze/stream` with a valid PDF
- **THEN** the system validates the PDF, runs the full pipeline, streams progress events, and completes with a redirect to the results page

#### Scenario: Successful analysis flow (non-streaming fallback)

- **WHEN** the user uploads a valid PDF via `POST /analyze`
- **THEN** the system validates the PDF, extracts text, detects skills, collects jobs, matches, validates links, generates reports, and renders the results page

#### Scenario: Invalid PDF rejected at analyze

- **WHEN** the user submits a non-PDF file to an analyze endpoint
- **THEN** the system returns an error without crashing
