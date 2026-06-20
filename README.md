# Career Market Fit Scanner

A local web app that compares your resume against real job postings from public APIs, classifies roles into career tracks, and generates market-fit reports with skill gaps and study recommendations.

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

## Optional: Ollama (LLM executive summary)

The PDF report includes an executive summary. With [Ollama](https://ollama.com/) running locally, the summary is generated from structured metrics only — never raw resume text or full job descriptions.

```bash
ollama pull llama3.2
ollama serve
```

Configure in `.env` (defaults shown):

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

If Ollama is unavailable, a deterministic template summary is used instead.

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
   - `reports/market_fit_report.pdf` — formatted PDF rendered from the markdown report (opens in browser when generated)

## PDF report setup (WeasyPrint)

PDF generation is included in `make setup`, which installs native libraries automatically:

- **macOS:** `brew install glib pango cairo gdk-pixbuf libffi` (via Homebrew)
- **Linux:** apt/dnf packages for Pango, Cairo, GLib (when available)

The app auto-detects Homebrew libraries on macOS. Run `make check` anytime to verify PDF support.

If WeasyPrint is unavailable, analysis still completes and the Markdown report is written; the results page shows a warning and PDF auto-open is skipped.

## Skill catalog and matching scope

- Skills are detected via regex word-boundary matching against `src/resume/skills.json`
- No TF-IDF, embeddings, or LLM for parsing or matching
- Job descriptions are matched using the same extractor on title + description
- Fit scores weight skills by tier (high/medium/low) with parent/child deduplication

## LLM scope

Ollama receives only a `ReportSummaryContext` JSON payload (counts, skill lists, top job summaries). It does **not** receive raw resume text or full job descriptions.

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
