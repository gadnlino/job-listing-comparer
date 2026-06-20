# Resume Parsing

Extracts text and skills from uploaded PDF resumes.

## Requirements

### Requirement: PDF resume upload and validation

The system SHALL accept a PDF file upload and reject non-PDF files with a clear error message.

#### Scenario: Valid PDF uploaded

- **WHEN** the user uploads a file with `.pdf` extension and valid PDF content
- **THEN** the system saves the file to `data/uploads/` and proceeds with text extraction

#### Scenario: Non-PDF file rejected

- **WHEN** the user uploads a file that is not a PDF
- **THEN** the system returns an error message indicating only PDF files are accepted

### Requirement: PDF text extraction

The system SHALL extract text from all pages of an uploaded PDF using `pypdf` or `pdfplumber` and save the result to `data/processed/resume_text.txt`.

#### Scenario: Successful text extraction

- **WHEN** a valid PDF with readable text is uploaded
- **THEN** the system extracts text from all pages and saves it to `data/processed/resume_text.txt`

#### Scenario: Invalid PDF handled gracefully

- **WHEN** an uploaded file is corrupted or unreadable as a PDF
- **THEN** the system returns a friendly error message without crashing

#### Scenario: PDF with no readable text

- **WHEN** a valid PDF contains no extractable text (e.g., scanned image-only)
- **THEN** the system returns a friendly warning that no text could be extracted

### Requirement: Deterministic skill extraction from resume

The system SHALL detect technical skills from extracted resume text using a shared skill catalog and regex-based keyword matching with word boundaries. No TF-IDF, NLP libraries, or LLM SHALL be used for skill extraction in v1.

#### Scenario: Known skills detected

- **WHEN** the resume text contains keywords such as "Python", "AWS", "Kubernetes", or "Terraform"
- **THEN** the system returns a list of detected skills with canonical name and confidence score

#### Scenario: Minimum skill catalog coverage

- **WHEN** skill extraction runs on any resume text
- **THEN** the system checks against a catalog including at minimum: Python, Node.js, TypeScript, JavaScript, AWS, AWS Lambda, API Gateway, DynamoDB, RDS, PostgreSQL, SQS, SNS, Docker, Kubernetes, Terraform, CI/CD, REST APIs, GraphQL, Microservices, Serverless, Security, IAM, Observability, CloudWatch, X-Ray, AI, LLM, RAG, Vector Database, Data Engineering, Kafka, Airflow, dbt

#### Scenario: Skill output includes confidence

- **WHEN** a skill is detected in the resume
- **THEN** the output includes the canonical skill name and a confidence score between 0 and 1

#### Scenario: Optional matched snippet

- **WHEN** a skill keyword is found in the resume text
- **THEN** the system MAY include a matched text snippet showing the surrounding context

### Requirement: Skill catalog file

The system SHALL load skill definitions from `src/resume/skills.json`. Each entry MUST include a canonical name, aliases, weight tier, and one or more regex patterns with word boundaries.

#### Scenario: Catalog loaded at startup

- **WHEN** the skill extractor initializes
- **THEN** the system loads and compiles regex patterns from `skills.json`

#### Scenario: Alias resolves to canonical name

- **WHEN** the resume text contains an alias such as "k8s" or "nodejs"
- **THEN** the system detects the corresponding canonical skill (e.g. Kubernetes, Node.js) in the output

### Requirement: Text normalization before skill matching

The system SHALL normalize resume text before matching by lowercasing and collapsing whitespace. Matching MUST be case-insensitive.

#### Scenario: Case-insensitive match

- **WHEN** the resume text contains "PYTHON" or "python"
- **THEN** the system detects the skill Python

### Requirement: Regex-based keyword matching with word boundaries

The system SHALL match skills using Python `re` with word-boundary patterns to reduce false positives on partial word matches.

#### Scenario: Word boundary prevents partial match

- **WHEN** the resume text contains "JavaScript" but not "Java"
- **THEN** the system detects JavaScript and does NOT detect Java

#### Scenario: Multi-word skill matched

- **WHEN** the resume text contains "AWS Lambda" or "REST APIs"
- **THEN** the system detects the corresponding multi-word canonical skill

### Requirement: Ambiguous skill token handling

The system SHALL apply catalog-defined rules for ambiguous or noisy tokens to avoid false positives.

#### Scenario: Short ambiguous tokens excluded

- **WHEN** the resume text contains common English words that are not technology skills
- **THEN** the system does NOT detect skills for tokens excluded from the catalog such as Go and R

#### Scenario: AI token requires word boundary

- **WHEN** the resume text contains "AI" as a standalone token
- **THEN** the system MAY detect the AI skill according to catalog rules; partial-word matches MUST NOT trigger detection

### Requirement: Skill deduplication

The system SHALL deduplicate detected skills by canonical name, keeping the match with the highest confidence when multiple aliases or patterns match the same skill.

#### Scenario: Duplicate alias matches deduplicated

- **WHEN** both "kubernetes" and "k8s" appear in the resume text
- **THEN** the system returns a single Kubernetes entry with the highest applicable confidence score

### Requirement: DetectedSkill output model

The system SHALL return each detected skill as a `DetectedSkill` object with canonical name, confidence score (0–1), weight tier from the catalog, and an optional matched text snippet.

#### Scenario: DetectedSkill fields populated

- **WHEN** a skill is successfully detected in resume text
- **THEN** the output includes `canonical_name`, `confidence`, `weight`, and optionally `snippet`

#### Scenario: Weight tier sourced from catalog

- **WHEN** a detected skill has a weight tier defined in `skills.json`
- **THEN** the `DetectedSkill.weight` field reflects that tier (high, medium, or low)
