## Context

The career-market-fit-scanner collects jobs from Remotive, Adzuna, and Arbeitnow, matches them to a resume, and renders results in the web UI plus CSV/Markdown/PDF reports. Job URLs come from each source's API:

| Source | URL field | Known issues |
|--------|-----------|--------------|
| Remotive | Direct job page URL | Occasionally expired listings |
| Adzuna | `redirect_url` (tracking/landing) | Redirect chains, geo blocks, expired ads |
| Arbeitnow | Direct apply/page URL | Less common failures |

Users reported that suggested links do not open in the browser. The app currently treats all URLs as valid and renders clickable "View" links with no verification.

## Goals / Non-Goals

**Goals:**

- Validate listing URL reachability before reports are written
- **Exclude confirmed-dead links** from UI, CSV, and report top-jobs output
- Preserve full match set for market stats and LLM executive summary
- Keep validation fast enough for local MVP (timeouts, concurrency cap, partial body read)
- Mock all outbound checks in tests

**Non-Goals:**

- Browser-based validation (Playwright/Selenium)
- Re-fetching job content or re-scraping listing pages
- Removing inaccessible jobs from fit scoring or market overview statistics
- Validating URLs at collection time (too early — jobs may expire before report)
- Periodic re-validation after report is generated

## Decisions

### 1. Validate after matching, before report generation

```
collect jobs → match all → validate links (GET) → split outputs
                              │
              ┌───────────────┴───────────────┐
              │                               │
    full match set                    display/export set
    (stats, LLM summary)              (accessible + unknown only)
```

**Rationale:** Validation is for the user's actionable output. Running once on the final match set avoids double work and reflects link state at report time. Market stats stay honest; user-facing links are trustworthy.

**Alternative considered:** Validate at collection — rejected; adds latency to collection and status may change before user views report.

### 2. Link status model

Add to `JobMatch`:

```python
LinkStatus = Literal["accessible", "inaccessible", "unknown"]

class JobMatch:
    ...
    link_status: LinkStatus = "unknown"
    link_status_code: int | None = None  # last HTTP status if checked
```

Propagate to `TopJobSummary` for reports and CSV column `link_status`.

**Rationale:** Keeps status on the match object used everywhere downstream.

### 3. HTTP validation strategy — GET only

Use `httpx` with:

- Method: **GET only** — no HEAD requests
- **Follow redirects** (max 5) — required for Adzuna
- **Stream response**: `stream=True`, read first **16 KB** max, then close — do not download full page
- **Timeout**: 5s connect, 10s total per URL
- **Concurrency**: max 10 parallel requests via thread pool or async client
- **Accessible** if final status is 2xx after redirects AND response body read exceeds **500 bytes**
- **Inaccessible** if 404, 410, 5xx, timeout, connection error, empty URL, or 2xx with body ≤ 500 bytes (empty/error landing page)
- **Unknown** if 403, 429, other 4xx (except 404/410), validation skipped (no URL, feature disabled, budget exceeded), or unexpected per-URL error

Do not send cookies. Use a simple identifiable User-Agent string.

**Rationale:** GET matches browser behavior; Adzuna and many aggregators reject or mishandle HEAD. Partial body read confirms the server returned a real page without downloading full HTML. 403/429 are kept as `unknown` because bot/geo blocking may succeed in the user's browser.

**Alternative considered:** HEAD first with GET fallback — rejected; false negatives on Adzuna and aggregators; user explicitly requested GET only.

### 4. Output filtering — drop inaccessible, keep unknown

| Output | Jobs included |
|--------|---------------|
| Market stats (jobs by source, track, skills) | All matches |
| LLM executive summary input | All matches |
| Results table (web UI) | `accessible` + `unknown` only |
| CSV export | `accessible` + `unknown` only |
| Markdown/PDF top jobs table | `accessible` + `unknown` only |

Inaccessible jobs are excluded from user-facing outputs. A summary note reports how many were excluded per source.

**Rationale:** User asked to drop inaccessible links. Keeping unknown (403/429) avoids over-aggressive removal when the validator cannot confirm death.

### 5. Validate all matched jobs, with optional cap

Default: validate **all jobs in the match list**.

If match count exceeds `LINK_VALIDATION_MAX_JOBS` (default 200), validate up to the cap; jobs beyond the cap get `unknown` and remain in output.

**Rationale:** User expects CSV links to be checked; cap prevents abuse on huge result sets.

### 6. UI and report presentation

| Surface | Behavior |
|---------|----------|
| Results table | Only accessible + unknown jobs shown; clickable "View" for accessible; neutral link for unknown |
| CSV | Only accessible + unknown rows; columns `link_status`, `link_status_code` |
| Markdown/PDF | Top jobs table from filtered set; footnote with excluded (inaccessible) count per source |
| Warnings | If >20% of a source's validated links are inaccessible: `"Adzuna: 45 of 109 links excluded — could not be verified"` |

Inaccessible jobs do **not** appear in the results table or CSV.

### 7. Configuration

Optional env vars in `.env.example`:

```env
LINK_VALIDATION_ENABLED=true
LINK_VALIDATION_MAX_JOBS=200
LINK_VALIDATION_TIMEOUT_SECONDS=10
LINK_VALIDATION_MIN_BODY_BYTES=500
```

Default enabled. Disable for offline/fast dev.

### 8. Failure isolation

Per-URL failures must not crash analysis. Validator catches all exceptions per URL and marks `unknown` (conservative — keep in output) unless status clearly indicates dead (404, 410, 5xx).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Slow analysis (many HTTP GET calls) | Concurrency cap, timeouts, partial body read (16 KB max) |
| False negatives (bot blocking, geo) | 403/429 → `unknown`, kept in output |
| False positives (200 empty shell page) | Minimum body size check (500 bytes) |
| Rate limiting by job boards | Conservative concurrency; identifiable User-Agent |
| Adzuna redirect false failures | Follow redirects; GET-only; document known limitations |
| Market stats vs output mismatch | Document that stats use full set; links use filtered set |

## Migration Plan

1. Add model fields with defaults (`unknown`) — backward compatible
2. Add validator module (GET-only, streaming)
3. Wire into analyze pipeline; add output filter for inaccessible jobs
4. Update templates and report generators
5. Add tests; update README

No database migration. Existing reports overwritten on next analysis.

## Open Questions

- _(none for MVP — GET-only, drop inaccessible from outputs, keep unknown)_
