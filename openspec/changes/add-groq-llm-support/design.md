## Context

The app generates executive summaries via `generate_llm_summary()` and PDFs via Markdown → HTML → WeasyPrint. Hosting exploration identified two server-side costs:

1. **LLM**: llama.cpp needs ~2–4 GB RAM — unsuitable for Railway free (~512 MB).
2. **PDF**: WeasyPrint causes ~100–250 MB render spikes and requires Pango/Cairo in Docker.

Groq’s free API (OpenAI-compatible, requires `LLM_API_KEY`) replaces local inference for cloud deploys. Browser PDF generation serves the same HTML used for WeasyPrint and triggers an automatic client-side PDF download on page load — no server PDF file and no in-app button.

## Goals / Non-Goals

**Goals:**

- Support Groq via `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`.
- Add `PDF_RENDERER=browser|weasyprint|off` with **browser auto-download** as the cloud default.
- Refactor shared `build_report_html(md_path)` used by WeasyPrint and browser routes.
- Auto-open printable report tab after analysis (same UX trigger as today’s PDF auto-open).
- Document Railway free-tier env profile (Groq + browser PDF + optional tuning).
- Remove unused `pandas`; keep WeasyPrint optional in Docker.
- Preserve local docker-compose + WeasyPrint path for full offline stack.

**Non-Goals:**

- Removing docker-compose / llama.cpp for local users.
- Groq SDK or streaming LLM changes.
- Silent save to disk with zero browser involvement (not possible — auto-download is closest).
- Replacing Markdown as source of truth.
- Server-side html2pdf (client-only).

## Decisions

### 1. `LLM_API_KEY` for all OpenAI-compatible providers

When set, attach `Authorization: Bearer` to `/v1/chat/completions` requests. Ollama fallback unchanged.

Recommended Groq env (documented, not hardcoded defaults):

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
```

### 2. `PDF_RENDERER` modes

| Value | Server behavior | Client behavior |
|-------|-----------------|-----------------|
| `browser` | Write `.md` only; serve `/report/print` HTML | New tab auto-opens; **on load, client library downloads `market_fit_report.pdf`** |
| `weasyprint` | Write `.md` + `.pdf` via WeasyPrint | Auto-open `/download/market_fit_report.pdf` (current) |
| `off` | Write `.md` only | No auto-open |

Default in code: `weasyprint` for backward compatibility locally; `.env.example` and Railway docs recommend `browser`.

`pdf_generated=True` when a printable report is available (browser or weasyprint mode with jobs).

### 3. Browser PDF: html2pdf.js auto-download on load

Print view route serves full report HTML (inline `report.css`). On `DOMContentLoaded`:

```javascript
html2pdf().set({ filename: 'market_fit_report.pdf', ... }).from(document.body).save();
```

Opened via `window.open('/report/print', '_blank')` from results page after analysis — same gesture chain as today (user clicked Analyze). No button in app UI.

**Rationale:** Meets “auto-download without user clicking a button” better than `window.print()`. Tradeoff: layout may differ slightly from WeasyPrint for wide tables — acceptable for cloud profile.

**Alternative:** `window.print()` on load — rejected; requires system print dialog confirmation.

### 4. Shared HTML builder

Extract from `pdf_renderer.py`:

```
market_fit_report.md
    → markdown → HTML fragment
    → Jinja2 report.html + report.css
    → full HTML string
         ├── weasyprint: HTML().write_pdf()
         └── browser: served at GET /report/print
```

### 5. Railway free-tier profile (documented)

Recommended env for ~512 MB hosts:

```env
PDF_RENDERER=browser
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
LINK_VALIDATION_ENABLED=false
LINK_VALIDATION_MAX_JOBS=25
```

Deploy **app Dockerfile only** (no llama sidecar). Use lower `max_results` in UI (e.g. 50) if memory is tight. Remove unused `pandas` from requirements.

Docker slim variant: omit WeasyPrint apt packages when targeting browser-only cloud images (document multi-stage or profile flag).

### 6. Remove unused `pandas`

Not imported anywhere in `src/` — safe removal reduces image size.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Groq 429 / outage | Ollama → template fallback; warning on results page |
| html2pdf quality on wide tables | Accept for cloud; use `weasyprint` locally for best PDF |
| Popup blocker on `window.open` | Keep manual link on results page (existing fallback pattern) |
| Download blocked without user gesture | Open tab from post-Analyze navigation chain (same as current PDF open) |
| API key in logs | Never log Authorization header |
| Two PDF code paths | Shared HTML builder; tests for both modes |

## Migration Plan

1. Implement config (`LLM_API_KEY`, `PDF_RENDERER`).
2. Refactor HTML builder; add `/report/print` + client JS.
3. Update pipeline, results auto-open logic, download links.
4. Remove pandas; update Dockerfile/docs for browser vs weasyprint.
5. Run `pytest`; manual smoke: Groq key + browser auto-download locally.

Rollback: `PDF_RENDERER=weasyprint` and unset Groq key for local stack.

## Open Questions

- None blocking. html2pdf options (margins, pagebreak) tuned during implementation if tables clip.
