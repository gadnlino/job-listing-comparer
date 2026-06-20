## Why

Users are clicking job links in analysis results and reports that fail to open — especially Adzuna `redirect_url` landing pages and expired listings. Broken links undermine trust in the market-fit report even when the underlying match data is useful. We need to validate listing URLs during report generation and **exclude confirmed-dead links** from user-facing outputs before the user clicks.

## What Changes

- Add a **link validation step** after job matching and before report generation that checks whether each job listing URL is reachable.
- Extend the data model with a per-job **link status** (`accessible`, `inaccessible`, `unknown`).
- Validate URLs via **HTTP GET only** (no HEAD) with redirects, streaming partial reads, timeouts, and bounded concurrency — no browser automation.
- **Drop** jobs with `inaccessible` links from UI results, CSV, and report top-jobs tables; keep them in the full match set for market stats and LLM summary.
- Treat **403 and 429** as `unknown` (keep in outputs) — these may work in the user's browser but fail for the validator.
- Add summary stats and warnings (e.g. "12 of 109 Adzuna links excluded — could not be verified").
- Limit validation scope to jobs included in outputs (all matches for CSV; optionally cap concurrent checks) to keep analysis time reasonable.
- Add tests with mocked HTTP responses; no live URL checks in CI.

## Capabilities

### New Capabilities

- `job-link-validation`: HTTP GET reachability checks for job listing URLs, link status model, validation orchestration with timeouts and concurrency limits, and filtering of inaccessible jobs from outputs.

### Modified Capabilities

- `report-generation`: Filter inaccessible jobs from CSV and top-jobs tables; include exclusion counts per source in Markdown/PDF.
- `web-app`: Show only accessible and unknown jobs in results table; warn when many links are excluded.
- `testing`: Tests for accessible, redirect, 404, timeout, 403-as-unknown, partial read, and filtering scenarios.

## Impact

- **Code**: New `src/analysis/link_validator.py`; extend `JobMatch` with link status; integrate in `src/app.py` analyze pipeline before `generate_reports()`; filter inaccessible jobs before report/UI output.
- **Models**: `LinkStatus` enum and optional fields on `JobMatch`, `TopJobSummary`, CSV columns.
- **Reports**: CSV excludes inaccessible rows; Markdown/PDF top-jobs table shows accessible + unknown only; exclusion summary per source.
- **Performance**: Adds N HTTP GET requests per analysis (bounded by match count and concurrency); may add 5–30s for large result sets. GET uses streaming with partial body read to limit bandwidth.
- **Dependencies**: Uses existing `httpx` only.
- **APIs**: No external API changes; outbound GET to job board URLs only.
