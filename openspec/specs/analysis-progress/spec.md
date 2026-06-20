# Analysis Progress

Progress reporting and streaming updates during analysis.

## Requirements

### Requirement: Analysis progress reporter

The system SHALL provide a `ProgressReporter` (or equivalent) that pipeline stages can call to emit structured progress updates with a human-readable message and optional fields: `stage`, `source`, `current`, `total`, and `title`.

#### Scenario: Reporter emits structured progress

- **WHEN** a pipeline stage calls the progress reporter during streaming analysis
- **THEN** the reporter records a progress update with at least a `message` field

#### Scenario: No-op reporter when not streaming

- **WHEN** analysis runs via non-streaming `POST /analyze`
- **THEN** pipeline stages MAY use a no-op reporter and behavior is unchanged

### Requirement: NDJSON streaming analyze endpoint

The system SHALL expose `POST /analyze/stream` accepting the same multipart form fields as `POST /analyze` and returning a newline-delimited JSON (NDJSON) response with progress events emitted while the pipeline runs.

#### Scenario: Progress events streamed during analysis

- **WHEN** a client POSTs a valid analyze request to `/analyze/stream`
- **THEN** the server emits one or more NDJSON lines with `"type":"progress"` before the pipeline completes

#### Scenario: Done event with redirect

- **WHEN** streaming analysis completes successfully
- **THEN** the server emits a final NDJSON line with `"type":"done"` and a `redirect` URL to the results page

#### Scenario: Error event on failure

- **WHEN** streaming analysis fails with a user-visible error (e.g. invalid PDF)
- **THEN** the server emits an NDJSON line with `"type":"error"` and a `message` field

### Requirement: Pipeline progress instrumentation

The system SHALL emit progress events at key pipeline stages when a progress reporter is provided.

#### Scenario: Collection progress per source

- **WHEN** job collection starts for a source during streaming analysis
- **THEN** a progress event indicates which source is being collected

#### Scenario: Match progress summary

- **WHEN** job matching runs during streaming analysis
- **THEN** a progress event indicates matching is in progress and includes the number of jobs matched when available

#### Scenario: Link validation progress per job

- **WHEN** link validation checks a job URL during streaming analysis
- **THEN** a progress event includes the job title, source, and current/total validation index (e.g. 23/109)

#### Scenario: Report generation progress

- **WHEN** reports are generated during streaming analysis
- **THEN** a progress event indicates report generation is in progress

