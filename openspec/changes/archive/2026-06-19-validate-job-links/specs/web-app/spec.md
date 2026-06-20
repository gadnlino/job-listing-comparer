## ADDED Requirements

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
