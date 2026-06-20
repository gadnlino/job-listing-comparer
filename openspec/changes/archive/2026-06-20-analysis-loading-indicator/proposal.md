## Why

Analysis can take 30 seconds or more (job collection, matching, link validation, report generation), but the UI gives no feedback after the user clicks **Analyze**. Users cannot see which job source or listing is being processed, the browser appears idle until the full results page loads, and duplicate submissions are likely.

## What Changes

- Add a **loading overlay** on the home page that appears immediately when the user submits the analyze form.
- Add a **streaming analyze endpoint** (`POST /analyze/stream`) that emits **NDJSON progress events** while the pipeline runs, then a final `done` event with a redirect URL to the results page.
- Introduce a **`ProgressReporter`** callback passed through collection, matching, link validation, and report generation to emit real stage messages.
- Show **live progress in the browser**: per-source collection, per-job link validation (title + source + counter), and report generation steps.
- Intercept form submit with **`fetch` + `FormData`** to read the NDJSON stream and update the overlay; navigate to results on `done`.
- **Disable** the submit button and form inputs while streaming to prevent double submissions.
- Keep **`POST /analyze`** as a non-streaming fallback for no-JavaScript clients (no live progress).
- Add styles in `styles.css` and client script in `index.html`.
- Add tests for stream event format, pipeline progress emission, and home page overlay contract.

## Capabilities

### New Capabilities

- `analysis-progress`: NDJSON streaming protocol, `ProgressReporter`, pipeline instrumentation for real-time progress events.

### Modified Capabilities

- `web-app`: Loading overlay driven by server progress stream; fetch-based form submit; results via redirect after stream completes.
- `job-link-validation`: Optional progress callback during per-URL validation (index/total, title, source).
- `testing`: Stream endpoint tests, progress event assertions, overlay + fetch submit contract tests.

## Impact

- **Code**: `src/app.py`, new `src/analysis/progress.py`, `src/collectors/orchestrator.py`, `src/analysis/link_validator.py`, `src/web/templates/index.html`, `src/web/static/styles.css`, `tests/test_web_app.py`, new `tests/test_analyze_stream.py`
- **APIs**: New `POST /analyze/stream` (NDJSON); existing `POST /analyze` retained as fallback
- **Dependencies**: None
- **UX**: Users see accurate progress including current job source and listing during link validation
