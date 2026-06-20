## ADDED Requirements

### Requirement: Streaming analyze endpoint tests

The system SHALL include tests for the NDJSON streaming analyze endpoint with mocked pipeline dependencies.

#### Scenario: Stream emits progress and done events

- **WHEN** `tests/test_analyze_stream.py` POSTs to `/analyze/stream` with a valid PDF and mocked externals
- **THEN** the response body contains at least one `type: progress` NDJSON line and a final `type: done` line with a redirect URL

#### Scenario: Stream emits error on invalid PDF

- **WHEN** the stream test POSTs a non-PDF file
- **THEN** the response contains an `type: error` NDJSON line or an appropriate HTTP error

#### Scenario: Link validation progress in stream

- **WHEN** the stream test runs with link validation enabled and mocked HTTP
- **THEN** at least one progress line includes `stage: validate` with title and source fields

### Requirement: Analysis loading indicator tests

The system SHALL include tests verifying the home page loading overlay and streaming submit contract.

#### Scenario: Home page includes loading overlay elements

- **WHEN** `tests/test_web_app.py` requests `GET /`
- **THEN** the response HTML includes the loading overlay container and status message element

#### Scenario: Home page includes streaming submit script

- **WHEN** the home page test runs
- **THEN** the response HTML includes client-side script that submits via fetch to `/analyze/stream` and updates the overlay from NDJSON progress events
