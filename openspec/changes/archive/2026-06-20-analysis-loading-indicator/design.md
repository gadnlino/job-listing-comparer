## Context

The app runs a synchronous analysis pipeline in `POST /analyze`: parse PDF → collect jobs → match → validate links → generate reports → render results HTML. Link validation alone can issue 100+ HTTP GETs (10 concurrent), taking most of the wait time. There is no logging or progress channel today.

Users want **real** progress in the browser — e.g. which source is being collected and which job listing URL is being validated — not guessed rotating messages.

## Goals / Non-Goals

**Goals:**

- Real-time progress visible in the browser during analysis
- Per-source messages during job collection
- Per-job messages during link validation (title, source, `{current}/{total}`)
- Immediate overlay on submit; form disabled until complete or error
- Plain HTML/CSS/minimal JS — no frontend framework
- Accessible loading state (`aria-live`, visible text)

**Non-Goals:**

- WebSockets or Server-Sent Events (SSE) — NDJSON stream on one `fetch` is sufficient
- Background job queue, job IDs, or polling endpoints
- Progress on the results page
- Cancel / abort in-flight analysis
- Showing full URLs in the overlay (title + company + source is enough)
- Server-side progress persistence across restarts

## Decisions

### 1. NDJSON stream on `POST /analyze/stream`

```
Browser                         Server
   │                               │
   │ fetch POST /analyze/stream    │
   │ (multipart FormData)          │
   │ ─────────────────────────────▶│
   │                               │ run pipeline; yield after each step
   │ ◀── {"type":"progress",...}\n │
   │ ◀── {"type":"progress",...}\n │
   │ ◀── {"type":"done","redirect":...}\n
   │                               │
   │ window.location = redirect    │
   ▼                               ▼
 results page                  (session stores result or redirect token)
```

**Response:** `Content-Type: application/x-ndjson` (or `application/json` with newline-delimited body).

**Event types:**

| type | fields | when |
|------|--------|------|
| `progress` | `message` (required), optional `stage`, `source`, `current`, `total`, `title` | Any pipeline step |
| `error` | `message` | Fatal failure; client hides overlay and shows error |
| `done` | `redirect` | Analysis complete; client navigates to results |

**Example lines:**

```json
{"type":"progress","stage":"parse","message":"Parsing resume…"}
{"type":"progress","stage":"collect","source":"adzuna","message":"Collecting jobs from Adzuna (gb)…"}
{"type":"progress","stage":"match","message":"Matching 109 jobs to your skills…"}
{"type":"progress","stage":"validate","source":"adzuna","current":23,"total":109,"title":"Senior ML Engineer","message":"Validating link 23/109: Senior ML Engineer (adzuna)"}
{"type":"progress","stage":"report","message":"Generating reports…"}
{"type":"done","redirect":"/analyze/result"}
```

**Rationale:** Single HTTP connection; server generator yields while processing; no in-memory job registry. Client reads with `response.body.getReader()`.

**Alternative considered:** SSE on separate URL — rejected; requires job store or duplicate connection handling.

**Alternative considered:** Fake client-side rotation — rejected; user requires accurate progress.

### 2. `ProgressReporter` callback

```python
class ProgressReporter:
    def emit(self, *, message: str, stage: str | None = None, ...) -> None: ...
```

- Passed optionally into `JobOrchestrator.collect()`, `validate_job_links()`, and report steps
- Default no-op reporter when not streaming (keeps `POST /analyze` simple)
- Stream endpoint wraps reporter to yield NDJSON lines

**Instrumentation points:**

| Location | Event |
|----------|-------|
| `app.py` / stream handler | `parse`, `skills` |
| `JobOrchestrator.collect()` | `collect` + `source` (Adzuna: include country when useful) |
| `match_jobs()` | `match` once with job count |
| `validate_job_links()` | `validate` per completed URL in `as_completed` loop |
| `generate_reports()` | `report` for Markdown and PDF steps |

Link validator change: accept optional `reporter` and `matches` metadata (title, source) when emitting per-job events.

### 3. Results delivery after stream

After pipeline completes, store `AnalysisResult` context in a **module-level or request-scoped session dict** keyed by short-lived token, OR render results to a temp session and expose `GET /analyze/result` that reads last completed result for this browser session.

**MVP choice:** In-memory `_last_analysis_result` + template context dict on the app module (single-user local app). Stream `done` redirects to `GET /analyze/result`. `POST /analyze` unchanged for fallback.

**Rationale:** Avoids sending full HTML inside NDJSON; keeps results page rendering logic in one place.

**Risk:** Single-user assumption — acceptable for local MVP per README.

### 4. Client: fetch submit + overlay update

- Intercept `form` `submit` with `preventDefault`
- Show overlay, disable form
- `fetch('/analyze/stream', { method: 'POST', body: new FormData(form) })`
- Read stream line-by-line; parse JSON; update `#loading-status` (and optional `#loading-detail` for counter)
- On `done`: `window.location.href = event.redirect`
- On `error`: hide overlay, show alert banner, re-enable form
- On network failure: same as error

Optional: show `current/total` as a simple progress bar when `total` is present.

### 5. Fallback `POST /analyze`

Keep existing synchronous endpoint for no-JS clients. Form `action` can remain `/analyze` with `<noscript>` note, or JS always hijacks when available.

### 6. Overlay UI

```html
<div id="analysis-loading" class="loading-overlay" hidden aria-live="polite" aria-busy="true">
  <div class="loading-panel">
    <div class="loading-spinner"></div>
    <p class="loading-title">Analyzing your resume…</p>
    <p id="loading-status" class="loading-status">Starting…</p>
    <p id="loading-detail" class="loading-detail" hidden></p>
  </div>
</div>
```

No rotating timer — all text from server events.

### 7. Testing

- `tests/test_analyze_stream.py`: mock pipeline steps; assert NDJSON lines include expected `stage`/`message`; assert `done` redirect
- Unit test `ProgressReporter` serialization
- Mock link validation with reporter; assert validate events include title/source/current/total
- `test_web_app.py`: overlay markup + fetch/stream script references on `GET /`
- Integration test: stream with mocked collectors/validator; read response body lines

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| In-memory result store not safe for multi-user | Document single-user MVP; session token if needed later |
| Stream interrupted mid-analysis | Client shows error; user retries |
| Verbose progress for 200+ links | Messages update in place (same line); optional throttle to 10 updates/sec max |
| Duplicate submit | Disable form on fetch start |
| JS disabled | Fallback `POST /analyze` without live progress |

## Migration Plan

1. Add `src/analysis/progress.py` and `POST /analyze/stream`
2. Instrument orchestrator and link validator
3. Add result handoff + `GET /analyze/result`
4. Update `index.html` + `styles.css` with fetch stream reader
5. Tests + manual verification with all sources enabled

## Open Questions

- _(none for MVP)_
