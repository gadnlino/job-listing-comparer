## 1. Progress Infrastructure

- [x] 1.1 Add `src/analysis/progress.py` with `ProgressReporter`, event dict helper, and NDJSON line formatter
- [x] 1.2 Add in-memory result handoff for streaming completion + `GET /analyze/result` (or equivalent redirect target)

## 2. Streaming Endpoint

- [x] 2.1 Implement `POST /analyze/stream` — NDJSON `StreamingResponse`, same form fields as `/analyze`
- [x] 2.2 Refactor analyze pipeline into a shared function callable from both `/analyze` and `/analyze/stream`
- [x] 2.3 Emit `progress`, `error`, and `done` events at parse, collect, match, validate, and report stages
- [x] 2.4 Keep `POST /analyze` as non-streaming fallback (no behavior regression)

## 3. Pipeline Instrumentation

- [x] 3.1 Pass optional `ProgressReporter` into `JobOrchestrator.collect()` — emit per-source (and Adzuna country when useful) messages
- [x] 3.2 Pass reporter into `validate_job_links()` — emit per completed URL with title, source, current/total
- [x] 3.3 Emit report-generation progress from `generate_reports()` or stream handler

## 4. Loading Overlay UI

- [x] 4.1 Add loading overlay markup to `index.html` (spinner, title, status, optional detail/counter, `aria-live` / `aria-busy`)
- [x] 4.2 Add overlay, spinner, and panel styles to `styles.css`

## 5. Client Streaming Behavior

- [x] 5.1 Intercept form submit — `fetch` + `FormData` to `/analyze/stream`, show overlay, disable form
- [x] 5.2 Read NDJSON stream with `response.body.getReader()`; update overlay from each `progress` event
- [x] 5.3 On `done`, navigate to redirect URL; on `error`/network failure, show error and re-enable form
- [x] 5.4 Remove generic message rotation (all text from server)

## 6. Tests and Verification

- [x] 6.1 Add `tests/test_analyze_stream.py` — progress + done events, validate stage fields, error on bad input
- [x] 6.2 Extend `tests/test_web_app.py` — overlay markup + streaming fetch script on `GET /`
- [x] 6.3 Update integration tests if result delivery path changes
- [x] 6.4 Run full pytest suite and fix failures
- [ ] 6.5 Manual verification — submit with all sources; confirm overlay shows real source and per-job validation messages until results load
