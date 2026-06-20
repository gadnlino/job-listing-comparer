## Why

Self-hosted LLM inference (llama.cpp / Ollama) and server-side WeasyPrint PDF rendering each require substantial RAM (~3–4 GB combined), which blocks cheap or free cloud hosting (e.g. Railway’s ~512 MB free tier). Groq provides a free OpenAI-compatible API sufficient for one executive summary per analysis. Browser-based PDF generation reuses the existing Markdown → HTML pipeline without WeasyPrint on the server, eliminating PDF memory spikes. Together, these changes enable deploying the app alone on lightweight hosts while preserving full local docker-compose for users who prefer self-hosted LLM and server PDF.

## What Changes

- Add `LLM_API_KEY` and `Authorization: Bearer` support for OpenAI-compatible LLM providers (Groq recommended for cloud).
- Add `PDF_RENDERER` configuration: `browser` (default for cloud), `weasyprint` (local/full server), or `off`.
- Add printable HTML report route built from canonical Markdown + `report.css`; auto-open in a new tab after analysis and **auto-download PDF in the browser** (no in-app button; uses client-side library on page load).
- Skip server-side WeasyPrint and `.pdf` file writes when `PDF_RENDERER=browser`; set `pdf_generated=True` when the printable report is available.
- Document **Railway free-tier profile**: Groq LLM, `PDF_RENDERER=browser`, optional link-validation tuning, app-only deploy (no docker-compose llama sidecar).
- Remove unused `pandas` dependency; slim production Docker image (optional WeasyPrint system libs only when `weasyprint` mode needed).
- Preserve fallback chain for LLM: OpenAI-compatible (optional API key) → Ollama → template summary.
- Preserve WeasyPrint path for local users who set `PDF_RENDERER=weasyprint`.
- Update tests and README accordingly.

## Capabilities

### New Capabilities

- `cloud-deployment`: Recommended environment profiles and constraints for deploying the app without llama.cpp or server-side PDF (Railway and similar hosts).

### Modified Capabilities

- `report-generation`: Groq/OpenAI-compatible LLM with API key; configurable PDF renderer (`browser` | `weasyprint` | `off`); browser printable HTML from canonical Markdown; server PDF optional.
- `web-app`: Auto-open printable report tab with client-side auto-download when `PDF_RENDERER=browser`; updated download links and LLM fallback wording.
- `testing`: Cover Groq auth headers, browser PDF mode (no WeasyPrint required in CI), and mocked client download path where applicable.

## Impact

- **Code**: `src/config.py`, `src/analysis/report_generator.py`, `src/analysis/pdf_renderer.py` (HTML builder refactor), `src/app.py` (print route), `src/web/templates/results.html`, new print template/JS, `Dockerfile`, `requirements.txt`, tests
- **Docs**: `README.md`, `.env.example`, Railway deploy section
- **Unchanged**: Job collection, matching, link validation logic (tunable via existing env vars), docker-compose for local self-hosted stack
- **Secrets**: `LLM_API_KEY` via environment only; Groq receives structured `ReportSummaryContext` JSON only
