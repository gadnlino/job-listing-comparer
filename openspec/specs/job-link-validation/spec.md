# Job Link Validation

Validates job listing URL reachability via HTTP GET before user-facing outputs are generated.

## Requirements

### Requirement: Job link validation module

The system SHALL provide a link validation module that checks job listing URL reachability using HTTP GET requests only.

#### Scenario: GET-only validation

- **WHEN** validating a job listing URL
- **THEN** the system sends an HTTP GET request (not HEAD) with redirect following and streaming enabled

#### Scenario: Partial body read

- **WHEN** a GET request returns a response body
- **THEN** the system reads at most 16 KB of the response body before closing the connection

#### Scenario: Empty URL skipped

- **WHEN** a job match has an empty or whitespace URL
- **THEN** link status is set to `inaccessible` without making an HTTP request

#### Scenario: Batch validation

- **WHEN** `validate_job_links(matches)` is called
- **THEN** the system validates all matches and returns the same list with `link_status` populated

#### Scenario: Status code captured

- **WHEN** an HTTP response is received during validation
- **THEN** the final status code is stored in `link_status_code` on the job match

#### Scenario: Accessible requires meaningful body

- **WHEN** a GET request completes with a 2xx status after redirects
- **THEN** the link is marked `accessible` only if the response body read exceeds the configured minimum byte threshold (default 500 bytes)

#### Scenario: Small body treated as inaccessible

- **WHEN** a GET request returns 2xx but the response body is at or below the minimum byte threshold
- **THEN** link status is set to `inaccessible`

#### Scenario: 403 and 429 treated as unknown

- **WHEN** a GET request returns HTTP 403 or 429
- **THEN** link status is set to `unknown` (not `inaccessible`)

#### Scenario: Display filter excludes inaccessible

- **WHEN** `filter_displayable_matches(matches)` is called after validation
- **THEN** the returned list includes only jobs with `link_status` of `accessible` or `unknown`

#### Scenario: Progress emitted per validated job

- **WHEN** `validate_job_links(matches, reporter=...)` is called during streaming analysis
- **THEN** the system emits a progress update for each completed URL check including job title, source, and current/total index
