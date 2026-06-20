## RENAMED Requirements

- FROM: `### Requirement: Local LLM executive summary`
- TO: `### Requirement: LLM executive summary`

## MODIFIED Requirements

### Requirement: LLM executive summary

The system SHALL generate a narrative executive summary for the report from the structured `ReportSummaryContext` only, using an OpenAI-compatible HTTP chat completions API when configured, with Ollama and deterministic template fallbacks.

#### Scenario: OpenAI-compatible provider generates executive summary

- **WHEN** `LLM_BASE_URL` is configured, the provider is reachable, and analysis completes with at least one job
- **THEN** the system sends a chat completion request to `{LLM_BASE_URL}/v1/chat/completions` with the structured context in the user message and receives a 2–3 paragraph executive summary for inclusion in the canonical Markdown report and printable output

#### Scenario: API key sent for authenticated providers

- **WHEN** `LLM_API_KEY` is set and the system calls the OpenAI-compatible chat completions endpoint
- **THEN** the request includes an `Authorization: Bearer` header with the configured key

#### Scenario: Groq configured as cloud provider

- **WHEN** the user sets `LLM_BASE_URL` to `https://api.groq.com/openai/v1`, a valid `LLM_API_KEY`, and a supported `LLM_MODEL`
- **THEN** the system generates the executive summary via Groq without requiring a local llama.cpp or Ollama server

#### Scenario: Local llama.cpp without API key

- **WHEN** `LLM_BASE_URL` points to a local OpenAI-compatible server (e.g. llama.cpp) and `LLM_API_KEY` is unset
- **THEN** the system calls chat completions without an Authorization header and uses the response when successful

#### Scenario: Ollama fallback after OpenAI-compatible failure

- **WHEN** the OpenAI-compatible request fails or returns no usable content
- **THEN** the system attempts Ollama via `{OLLAMA_BASE_URL}/api/generate` before falling back to the template summary

#### Scenario: LLM unavailable fallback

- **WHEN** all configured LLM providers are unreachable or return errors
- **THEN** the system generates a deterministic template executive summary from the same structured context and still produces the Markdown report and printable output when jobs were matched

#### Scenario: LLM does not alter deterministic sections

- **WHEN** the report is generated
- **THEN** tables, skill lists, top jobs, and study recommendation are rendered deterministically from computed data — only the executive summary narrative section uses LLM output

## MODIFIED Requirements

### Requirement: Summary PDF report

The system SHALL produce a summary PDF view of the canonical `market_fit_report.md` using either server-side WeasyPrint (`PDF_RENDERER=weasyprint`) or client-side browser generation (`PDF_RENDERER=browser`). The PDF content SHALL match the Markdown report. When `PDF_RENDERER=off`, no PDF is produced.

#### Scenario: Server PDF via WeasyPrint

- **WHEN** `PDF_RENDERER=weasyprint`, analysis completes with at least one job match, and WeasyPrint is available
- **THEN** the system writes `reports/market_fit_report.pdf` rendered from `market_fit_report.md`

#### Scenario: Browser PDF without server file

- **WHEN** `PDF_RENDERER=browser` and analysis completes with at least one job match
- **THEN** the system writes `market_fit_report.md` and serves printable HTML at `GET /report/print` but does not require a server-side `.pdf` file

#### Scenario: PDF sections included

- **WHEN** a summary PDF is produced (server or browser path)
- **THEN** it includes: title and date, executive summary (LLM or template fallback), resume skills, market overview tables, top missing skills, per-source snapshot table, top 20 matching jobs table (accessible and unknown only), deterministic study recommendation, and job source attribution (including Remotive credit where applicable)

#### Scenario: PDF not generated when no jobs found

- **WHEN** analysis completes with zero job matches
- **THEN** the system does not offer PDF generation and shows a friendly message on the results page

#### Scenario: WeasyPrint unavailable in weasyprint mode

- **WHEN** `PDF_RENDERER=weasyprint`, job matches exist, but WeasyPrint cannot render
- **THEN** the system still writes `market_fit_report.md`, skips server PDF, sets `pdf_generated=False`, and adds a warning explaining how to install WeasyPrint dependencies

## MODIFIED Requirements

### Requirement: Markdown-first PDF rendering pipeline

The system SHALL build printable report output using a Markdown-first pipeline: write canonical Markdown, convert to HTML with `report.css`, then render PDF via WeasyPrint when `PDF_RENDERER=weasyprint` or defer PDF rendering to the browser when `PDF_RENDERER=browser`. The system SHALL NOT use fpdf2 for report generation.

#### Scenario: Pipeline steps for server PDF mode

- **WHEN** report generation runs with at least one job match and `PDF_RENDERER=weasyprint`
- **THEN** the system first writes `market_fit_report.md`, then converts that Markdown to HTML wrapped in a report template with `report.css`, then renders PDF via WeasyPrint

#### Scenario: Pipeline steps for browser PDF mode

- **WHEN** report generation runs with at least one job match and `PDF_RENDERER=browser`
- **THEN** the system writes `market_fit_report.md` and makes the same Markdown → HTML conversion available via `GET /report/print` without invoking WeasyPrint on the server

#### Scenario: CSS controls report layout

- **WHEN** printable HTML is produced (for WeasyPrint or browser)
- **THEN** typography, heading hierarchy, table borders, page margins, and URL wrapping are controlled by `src/analysis/templates/report.css`

## MODIFIED Requirements

### Requirement: Local report storage

The system SHALL store generated reports locally as CSV and Markdown without using a database. A server-side PDF file SHALL be written only when `PDF_RENDERER=weasyprint` and rendering succeeds.

#### Scenario: Reports overwritten on new analysis

- **WHEN** a new analysis is run
- **THEN** previous reports in `reports/` are overwritten with the new results

## ADDED Requirements

### Requirement: Browser PDF auto-download

The system SHALL support client-side PDF generation in the user's browser when `PDF_RENDERER=browser`, automatically triggering a PDF download without requiring the user to click an in-app button.

#### Scenario: Printable HTML route available

- **WHEN** analysis completes with at least one job match and `PDF_RENDERER=browser`
- **THEN** the system serves `GET /report/print` as a print-ready HTML page built from the current `market_fit_report.md`

#### Scenario: Auto-download on print page load

- **WHEN** the printable HTML page loads in the browser after being opened from the post-analysis flow
- **THEN** client-side JavaScript automatically generates and downloads `market_fit_report.pdf` without an in-app "Save as PDF" button

#### Scenario: Markdown remains source of truth

- **WHEN** browser PDF mode is used
- **THEN** the downloadable PDF is derived from the same canonical Markdown content written in that analysis run

## MODIFIED Requirements

### Requirement: PDF report download endpoint

The system SHALL provide a download endpoint for the server-generated summary PDF when `PDF_RENDERER=weasyprint`.

#### Scenario: PDF download available in weasyprint mode

- **WHEN** the user requests `GET /download/market_fit_report.pdf`, `PDF_RENDERER=weasyprint`, and the file exists
- **THEN** the system returns the PDF file with `Content-Type: application/pdf` and `Content-Disposition: inline` so the browser displays it in a new tab

#### Scenario: PDF download friendly error when missing

- **WHEN** the user requests `GET /download/market_fit_report.pdf` and the file does not exist
- **THEN** the system returns a friendly error message indicating the file is not available

#### Scenario: Browser mode uses print route instead

- **WHEN** `PDF_RENDERER=browser` and the user needs a PDF after analysis
- **THEN** the system directs the user to the auto-download printable route rather than a server `.pdf` file
