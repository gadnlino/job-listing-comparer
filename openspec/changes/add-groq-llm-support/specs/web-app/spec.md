## MODIFIED Requirements

### Requirement: Report download links on results page

The system SHALL display links on the results page to download generated CSV and Markdown reports, and to access the summary PDF (server file or browser printable route depending on `PDF_RENDERER`).

#### Scenario: Download links visible after analysis

- **WHEN** analysis completes and reports are generated
- **THEN** the results page shows links to download `job_matches.csv` and `market_summary.md`, and a link to open or download the summary PDF when a printable report is available

#### Scenario: PDF link omitted when not available

- **WHEN** analysis completes with zero job matches or `PDF_RENDERER=off`
- **THEN** the results page does not show a summary PDF link

#### Scenario: LLM fallback warning displayed

- **WHEN** the report was generated using template fallback because no LLM provider (OpenAI-compatible or Ollama) returned a usable summary
- **THEN** the results page displays a friendly warning that the LLM summary was unavailable

## MODIFIED Requirements

### Requirement: Auto-open PDF report in new tab

The system SHALL automatically open a new browser tab for the summary report when analysis completes and a printable report is available (`pdf_generated=True`). Implementation uses inline JavaScript in `results.html` (no frontend framework).

#### Scenario: Server PDF auto-opens in weasyprint mode

- **WHEN** analysis completes, `PDF_RENDERER=weasyprint`, and a server PDF was generated
- **THEN** the results page includes an inline script that calls `window.open('/download/market_fit_report.pdf', '_blank')` on page load

#### Scenario: Browser PDF auto-opens print route

- **WHEN** analysis completes and `PDF_RENDERER=browser` with at least one job match
- **THEN** the results page includes an inline script that calls `window.open('/report/print', '_blank')` on page load, which triggers client-side auto-download of `market_fit_report.pdf`

#### Scenario: Popup blocked fallback displayed

- **WHEN** the browser blocks the automatic popup (`window.open` returns null)
- **THEN** the results page displays a prominent manual link to open the printable report or server PDF

#### Scenario: No auto-open when report not available

- **WHEN** analysis completes with zero job matches or `PDF_RENDERER=off`
- **THEN** the results page does not include the auto-open script

#### Scenario: Results page remains visible in current tab

- **WHEN** the report auto-open succeeds
- **THEN** the results page remains displayed in the current browser tab while the report opens in a separate tab
