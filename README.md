# Career Market Fit Scanner

A local web app that compares your resume against real job postings from public APIs, classifies roles into career tracks, and generates market-fit reports with skill gaps and study recommendations.

**Live demo:** [job-listing-comparer-production.up.railway.app](https://job-listing-comparer-production.up.railway.app/)  
**Project site:** [gadnlino.github.io/job-listing-comparer](https://gadnlino.github.io/job-listing-comparer/) (GitHub Pages — enable after merge; see below)

## What it does

1. Upload a resume PDF
2. Extract skills using a curated keyword catalog (`src/resume/skills.json`)
3. Collect jobs from Remotive, Arbeitnow, and optionally Adzuna
4. Score fit per job (0–100), classify career tracks, and rank missing skills
5. Display results in the browser and write reports to `reports/`

## Quick start

Works out of the box with **Remotive** and **Arbeitnow** — no API keys required.

```bash
make setup          # everything: system libs, venv, deps, dirs, .env, verify
make run            # http://127.0.0.1:8000
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload
```

Open http://127.0.0.1:8000, upload a PDF resume, and click **Analyze**.

## Optional: Adzuna

Adzuna requires free API credentials. Without them, the app skips Adzuna and shows a warning.

1. Register at https://developer.adzuna.com/
2. Copy `.env.example` to `.env`
3. Set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

## Optional: Link validation

After matching, the app validates job listing URLs with HTTP **GET** requests (streaming, partial body read) before generating reports. Jobs with confirmed-dead links (404, timeout, empty page) are **excluded** from the results table, CSV, and report top-jobs section. Market overview statistics still use the full matched set.

Configure in `.env` (defaults shown):

```env
LINK_VALIDATION_ENABLED=true
LINK_VALIDATION_MAX_JOBS=200
LINK_VALIDATION_TIMEOUT_SECONDS=10
LINK_VALIDATION_MIN_BODY_BYTES=500
```

403/429 responses are treated as unverified — those jobs are kept. Set `LINK_VALIDATION_ENABLED=false` to skip checks entirely.

## Optional: LLM executive summary (llama.cpp or Ollama)

The PDF report includes an executive summary. With a local LLM server running, the summary is generated from structured metrics only — never raw resume text or full job descriptions.

### Option A: llama.cpp server (recommended for Docker Compose)

This repo includes a `docker-compose.yml` that runs:
- `app` (FastAPI)
- `llama` (llama.cpp `llama-server`, OpenAI-compatible API)

1. Put a GGUF model at `./models/model.gguf`
2. Run:

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000`.

#### Auto-download a simple default model (Phi-2)

If you don't want to manually download a model, the default `docker-compose.yml` will download a small CPU-friendly GGUF on first run (Phi-2 Q4_K_M) into `./models/model.gguf`.

To change the model, set `MODEL_URL` to a direct `.gguf` download URL:

```bash
MODEL_URL="https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf" docker compose up --build
```

Configure via `.env` (defaults shown):

```env
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=default
```

### Option B: Ollama (backwards compatible)

```bash
ollama pull llama3.2
ollama serve
```

Configure in `.env` (defaults shown):

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

If the LLM server is unavailable, a deterministic template summary is used instead.

### Option C: Groq (recommended for cloud deploy)

[Groq](https://console.groq.com) offers a free tier (no credit card) with an OpenAI-compatible API — enough for one executive summary per analysis.

1. Create an account at https://console.groq.com
2. Generate an API key
3. Add to `.env`:

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_your_key_here
```

Groq receives only the structured `ReportSummaryContext` JSON (counts, skill lists, top job summaries) — not raw resume text or full job descriptions.

When using Groq, you do **not** need the docker-compose `llama` sidecar.

## PDF rendering (`PDF_RENDERER`)

Reports are authored as Markdown first (`reports/market_fit_report.md`). PDF output mode is controlled by `PDF_RENDERER`:

| Mode | Behavior |
|------|----------|
| `weasyprint` (default) | Server writes `market_fit_report.pdf` via WeasyPrint; auto-opens in a new tab |
| `browser` | Server serves printable HTML at `/report/print`; your browser auto-downloads the PDF (no WeasyPrint on server) |
| `off` | Markdown + CSV only |

```env
PDF_RENDERER=weasyprint
```

For lightweight cloud hosts (Railway, Render, etc.), use **`PDF_RENDERER=browser`** to avoid WeasyPrint RAM usage.

After analysis with `browser` mode, the results page automatically opens `/report/print`, which triggers a client-side PDF download — no button click required.

## Cloud deploy: Railway

**Production:** [https://job-listing-comparer-production.up.railway.app/](https://job-listing-comparer-production.up.railway.app/)

Deploy the **app Dockerfile only** (not full `docker-compose`). Recommended env:

```env
PDF_RENDERER=browser
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
LINK_VALIDATION_ENABLED=false
LINK_VALIDATION_MAX_JOBS=25
```

Tips for ~512 MB RAM:

- Use Groq instead of a local LLM container
- Use `PDF_RENDERER=browser` instead of WeasyPrint
- Lower **max results** in the UI (e.g. 50)
- Optionally disable link validation (shown above)

The production Docker image omits WeasyPrint system libraries when you only need browser PDF mode — set `PDF_RENDERER=browser` on the platform.

## GitHub Pages landing site

A static marketing page lives in `docs/` and is published via GitHub Pages after merging to `main`.

**Expected URL:** [https://gadnlino.github.io/job-listing-comparer/](https://gadnlino.github.io/job-listing-comparer/)

The landing page links to the live Railway app. It does not host the analyzer — GitHub Pages serves static HTML only.

### Enable GitHub Pages (one-time, after merge)

1. Merge the `docs/` changes to `main`
2. GitHub → **Settings** → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **`main`**, folder: **`/docs`**
5. Save and wait ~1–2 minutes for the site to build

To preview locally before merge, open `docs/index.html` in a browser (or use a simple static server).

## Platform authentication

| Source     | Auth required | Notes                                      |
|-----------|---------------|--------------------------------------------|
| Remotive  | No            | Public API; include attribution on results |
| Arbeitnow | No            | Public job board API                       |
| Adzuna    | Yes           | `app_id` + `app_key` query parameters      |
| Ollama    | No (local)    | HTTP to localhost only                     |

## API rate limits

- **Remotive:** ~4 requests/day for the public API. This app uses **one batch call** per analysis (`category=software-dev`) and filters client-side to stay within limits.
- **Adzuna:** Per your developer plan; the app paginates search results per query/country.
- **Arbeitnow:** Public API; paginated fetch with client-side query filtering.

## Usage workflow

1. Choose max results, job source(s), and Adzuna country filter
2. Upload a PDF resume and submit
3. Review summary cards, track breakdown, top jobs, and the verified job table (inaccessible links excluded)
4. Download reports:
   - `reports/job_matches.csv` — verified match table with link status columns
   - `reports/market_fit_report.md` — canonical markdown report (also served at `/download/market_summary.md`)
   - PDF — server file with `PDF_RENDERER=weasyprint`, or browser auto-download with `PDF_RENDERER=browser`

## PDF report setup (WeasyPrint — `PDF_RENDERER=weasyprint` only)

When using server-side PDF (`PDF_RENDERER=weasyprint`), native libraries are required:

- **macOS:** `brew install glib pango cairo gdk-pixbuf libffi` (via Homebrew)
- **Linux:** apt/dnf packages for Pango, Cairo, GLib (when available)

The app auto-detects Homebrew libraries on macOS. Run `make check` anytime to verify PDF support.

If WeasyPrint is unavailable, analysis still completes and the Markdown report is written; switch to `PDF_RENDERER=browser` or accept no server PDF.

## Skill catalog and matching scope

- Skills are detected via regex word-boundary matching against `src/resume/skills.json`
- No TF-IDF, embeddings, or LLM for parsing or matching
- Job descriptions are matched using the same extractor on title + description
- Fit scores weight skills by tier (high/medium/low) with parent/child deduplication

## LLM scope

Configured LLM providers (Groq, llama.cpp, or Ollama) receive only a `ReportSummaryContext` JSON payload (counts, skill lists, top job summaries). They do **not** receive raw resume text or full job descriptions.

## Testing

All external APIs are mocked in tests:

```bash
make test
# or: python3 -m pytest
```

## MVP limitations

- Keyword-based matching only (no semantic similarity)
- No user accounts or history
- Sequential job collection (no background workers)
- Remotive batch limited to `software-dev` category
- PDF parsing quality depends on resume PDF text layer
- Local single-user filesystem storage

## Roadmap

- Additional job sources via the collector interface
- Improved PDF extraction (e.g. pdfplumber)
- Async collectors and caching
- Configurable skill catalog UI

## Remotive attribution

Job data from Remotive is attributed on the results page and in generated PDF reports, per Remotive API terms.
