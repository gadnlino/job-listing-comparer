## ADDED Requirements

### Requirement: Shared skill extractor for jobs

The system SHALL extract skills from job postings using the same `extract_skills()` function and `skills.json` catalog used for resume parsing. Job skill extraction MUST run on the concatenation of job title and job description.

#### Scenario: Job skills extracted via shared catalog

- **WHEN** a job posting title or description contains skill keywords
- **THEN** the system detects skills using the same catalog, regex patterns, and normalization rules as resume extraction

#### Scenario: Title and description both scanned

- **WHEN** skills appear only in the job description or only in the title
- **THEN** the system detects those skills from the combined title + description text

### Requirement: Career track classification

The system SHALL classify each job posting into one or more career tracks using keyword matching against predefined track definitions.

#### Scenario: Five career tracks defined

- **WHEN** track classification runs
- **THEN** the system evaluates jobs against these tracks: backend_cloud, ai_engineering, cloud_security, platform_engineering, data_engineering

#### Scenario: Multi-track assignment

- **WHEN** a job description matches keywords from multiple career tracks
- **THEN** the job is assigned to all matching tracks with individual track scores

#### Scenario: Primary track selection

- **WHEN** a job matches one or more career tracks
- **THEN** the system sets `primary_track` to the track with the highest score

### Requirement: Resume-to-job fit scoring

The system SHALL calculate a fit score from 0 to 100 for each job by comparing resume skills against job skills extracted via the shared skill catalog. Weights MUST come from `skills.json` weight tiers.

#### Scenario: Matched skills increase fit score

- **WHEN** a skill is present in both the resume and the job posting
- **THEN** the fit score increases proportionally to the skill's weight tier from `skills.json`

#### Scenario: Missing skills identified

- **WHEN** a skill is detected in the job but not in the resume
- **THEN** the skill appears in the job's `missing_skills` list

#### Scenario: Weighted skill tiers from catalog

- **WHEN** calculating fit score
- **THEN** the system applies weights defined in `skills.json`, including high weight for skills such as IAM, Kubernetes, Terraform, RAG, Vector Database, Kafka, Observability, DevSecOps; medium weight for Python, Node.js, TypeScript, AWS, Docker, PostgreSQL, Microservices, Serverless; and lower weight for JavaScript

#### Scenario: Parent and child skills do not double-count

- **WHEN** both a parent skill (e.g. AWS) and a child skill (e.g. AWS Lambda) are detected in the same job or resume
- **THEN** the fit score counts only the most specific skill's weight, not both

#### Scenario: Fit score bounded 0-100

- **WHEN** fit score calculation completes
- **THEN** the resulting `fit_score` is a number between 0 and 100 inclusive

### Requirement: Seniority estimation

The system SHALL estimate job seniority level from title and description keywords.

#### Scenario: Seniority levels detected

- **WHEN** a job title contains keywords such as "Junior", "Senior", "Staff", "Principal", "Lead", or "Engineering Manager"
- **THEN** the system sets `seniority_estimate` to the corresponding value: junior, mid, senior, staff, principal, lead, manager, or unknown

#### Scenario: Title prioritized over description

- **WHEN** seniority keywords appear in both title and description
- **THEN** the system prioritizes the title for seniority estimation

### Requirement: JobMatch data model

The system SHALL produce a `JobMatch` object for each analyzed job containing: job (JobPosting), primary_track, track_scores, fit_score, matched_skills, missing_skills, seniority_estimate.

#### Scenario: Complete match object produced

- **WHEN** a job is analyzed against a resume
- **THEN** the system produces a `JobMatch` with all required fields populated

### Requirement: Market demand aggregation

The system SHALL aggregate analysis results to compute market demand metrics by career track and skill frequency across all collected jobs.

#### Scenario: Jobs counted by track

- **WHEN** analysis completes for multiple jobs
- **THEN** the system counts the number of jobs per career track

#### Scenario: Top requested skills ranked

- **WHEN** analysis completes
- **THEN** the system ranks the top 20 most frequently requested skills across all jobs

#### Scenario: Top missing skills ranked

- **WHEN** analysis completes against a resume
- **THEN** the system ranks the top 20 skills most frequently missing from the resume across analyzed jobs
