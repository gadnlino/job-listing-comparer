## ADDED Requirements

### Requirement: Link validator unit tests

The system SHALL include unit tests for the link validation module with mocked HTTP responses.

#### Scenario: Accessible 200 response with body

- **WHEN** `tests/test_link_validator.py` runs with a mocked 200 response and body exceeding the minimum byte threshold
- **THEN** the job match is marked `accessible`

#### Scenario: Inaccessible 404 response

- **WHEN** the test runs with a mocked 404 response
- **THEN** the job match is marked `inaccessible`

#### Scenario: Timeout handled

- **WHEN** the test runs with a mocked timeout
- **THEN** the job match is marked `inaccessible` and analysis does not raise

#### Scenario: Redirect followed

- **WHEN** the test runs with a mocked 302 redirect to a 200 destination with sufficient body
- **THEN** the job match is marked `accessible`

#### Scenario: 403 treated as unknown

- **WHEN** the test runs with a mocked 403 response
- **THEN** the job match is marked `unknown`

#### Scenario: Small body treated as inaccessible

- **WHEN** the test runs with a mocked 200 response and body below the minimum byte threshold
- **THEN** the job match is marked `inaccessible`

#### Scenario: Display filter excludes inaccessible

- **WHEN** the test runs `filter_displayable_matches()` on a mix of accessible, inaccessible, and unknown matches
- **THEN** inaccessible matches are excluded and accessible/unknown matches are retained

### Requirement: Report output reflects link filtering tests

The system SHALL verify link status and filtering appear in generated reports.

#### Scenario: CSV includes link_status column and excludes inaccessible

- **WHEN** report CSV tests run after validation with mixed link statuses
- **THEN** they assert `link_status` and `link_status_code` columns are present and inaccessible rows are omitted

#### Scenario: Integration test mocks link validation

- **WHEN** `tests/test_integration_pipeline.py` runs
- **THEN** link validation HTTP GET calls are mocked and results include link status fields with inaccessible jobs filtered from outputs

## MODIFIED Requirements

### Requirement: Test suite runs without external services

The system SHALL include a pytest suite that validates all capabilities without requiring live calls to external job APIs, Ollama, or job listing URLs.

#### Scenario: All externals mocked

- **WHEN** `pytest` runs
- **THEN** all tests pass without live calls to Remotive, Adzuna, Arbeitnow, Ollama, or job listing URLs
