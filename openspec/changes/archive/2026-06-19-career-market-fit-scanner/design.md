## Context

This is a greenfield local web application for a backend/cloud developer who wants data-driven guidance on which technical specializations to pursue next. The tool compares a resume PDF against job postings from public APIs (Remotive, Adzuna, Arbeitnow), classifies jobs into career tracks, and produces a market-fit report.

Constraints from the MVP scope:
- Python 3.11+, FastAPI, Jinja2, no frontend framework
- No database, auth, deployment, background workers, or scraping
- Deterministic keyword-based matching for skills and fit scoring
- Local LLM (Ollama) for PDF executive summary narrative only — never for parsing, matching, or classification
- Local filesystem for uploads, intermediate data, and reports
- Graceful degradation when API sources fail or Adzuna credentials are missing

## Goals / Non-Goals

**Goals:**

- End-to-end flow: upload PDF → extract skills → collect jobs → match → display results → download reports
- Modular collector architecture extensible to future job sources
- Fault-tolerant multi-source job collection with per-source warnings
- Deterministic, testable matching and classification logic
- LLM-generated executive summary in PDF report from structured computed data only
- Simple, readable web UI with Jinja2 templates

**Non-Goals:**

- Semantic/embedding-based matching
- TF-IDF or statistical similarity scoring
- NLP libraries (spaCy, skillNER, etc.)
- LLM for skill extraction, job matching, or career track classification
- Cloud LLM APIs (OpenAI, Anthropic, etc.)
- Sending raw job descriptions or resume text to the LLM
- LinkedIn or web scraping
- User accounts or persistent session history
- Production deployment or Docker packaging
- Real-time job monitoring or scheduled background fetches

## Decisions

### 1. Project layout: flat `src/` package tree

Use the user-specified structure with modules grouped by concern (`resume/`, `collectors/`, `analysis/`, `web/`). Single FastAPI app entry point at `src/app.py`.

**Rationale:** Matches the user's expected layout; keeps modules discoverable without over-abstracting.

**Alternative considered:** Single-file monolith — rejected because collectors and analysis are independently testable.

### 2. HTTP client: `httpx`

Use `httpx` for async-capable HTTP calls to job APIs. Collectors can run synchronously in the MVP (called from sync route handlers) but `httpx` keeps the door open for async later.

**Alternative considered:** `requests` — simpler but less flexible; both are acceptable; `httpx` is modern default.

### 3. PDF parsing: `pypdf`

Use `pypdf` for text extraction — lighter dependency than `pdfplumber`, sufficient for MVP resume parsing.

**Alternative considered:** `pdfplumber` — better layout handling but heavier; can swap later if extraction quality is poor.

### 4. Collector pattern: abstract base class

Define `BaseCollector` with `search_jobs(query, max_results, **kwargs) -> list[JobPosting]`. Each source implements normalization internally and stores raw API payload in `JobPosting.raw_payload`.

**Rationale:** Common interface enables orchestration layer to iterate sources uniformly and handle failures per-collector.

### 5. Job orchestration: sequential collection with error isolation

A `JobOrchestrator` (or inline logic in the analyze endpoint) calls each selected collector in sequence, catching exceptions per source. Failed sources produce warnings; successful sources contribute jobs. Results are deduplicated by `(source, id)` or `(title, company, url)`.

Each source uses a different fetch strategy tuned to its API constraints (see Decision 17).

**Rationale:** No background workers in MVP; sequential is simpler and sufficient for ~100 jobs per source.

### 6. Default search strategy: predefined query list with source-specific fetch

Run 13 default search queries for filtering and matching. How queries map to API calls differs by source:

| Source | Fetch strategy | API calls per analysis |
|---|---|---|
| **Remotive** | Single `GET` with `category=software-dev`; filter client-side against all 13 query keywords | **1 call** |
| **Adzuna** | One API call per query × country (credentials required); paginate as needed | Multiple (has own rate limits) |
| **Arbeitnow** | Paginated `GET`; filter client-side against query keywords | 1–few calls |

**Remotive rate limit:** The public API recommends a maximum of ~4 calls per day. A single batch fetch per analysis run avoids exceeding this limit when running 13 default queries.

**Rationale:** User's target roles are backend/cloud/AI/security — predefined queries capture market breadth. Client-side filtering on Remotive and Arbeitnow respects platform usage terms without sacrificing query coverage.

For Adzuna, iterate over selected countries (default: gb, us, es, de, nl, ie) with reduced results per country to stay within max_results.

### 7. Skill extraction: catalog + regex (v1)

Use a shared, deterministic skill extraction engine for both resume text and job postings (title + description). No TF-IDF, NLP libraries, or LLM in v1.

**Tools:**
- **Skill catalog:** `src/resume/skills.json` — canonical skill names, aliases, weight tiers, and optional regex patterns
- **Matching:** Python `re` with word-boundary patterns (`\b...\b`) compiled at load time
- **Normalization:** Python stdlib (`str.lower()`, whitespace collapse) before matching
- **Module:** `src/resume/skill_extractor.py` with `extract_skills(text: str) -> list[DetectedSkill]`
- **Model:** `DetectedSkill` Pydantic model with `canonical_name`, `confidence` (0–1), `weight` (high/medium/low), optional `snippet`

**Skill catalog shape (conceptual):**

```json
{
  "canonical_name": "Kubernetes",
  "aliases": ["k8s", "kube"],
  "weight": "high",
  "patterns": ["\\bkubernetes\\b", "\\bk8s\\b"]
}
```

**Extraction pipeline:**

```
raw text
  → lowercase
  → collapse whitespace
  → for each skill in skills.json:
       match canonical name and aliases via word-boundary regex
       if match: record canonical name, confidence, optional snippet
  → dedupe by canonical name (keep highest confidence)
  → apply parent/child rules (e.g. AWS Lambda match does not double-count AWS weight in fit scoring)
```

**Confidence rules (explainable, not statistical):**

| Match type | Base confidence |
|---|---|
| Exact canonical term with word boundary | 1.0 |
| Known alias (e.g. `k8s` → Kubernetes) | 0.9 |
| Parent skill when child also matched (e.g. `AWS` when `AWS Lambda` present) | 0.85 |
| Ambiguous short token (`AI`) without context | 0.6 or skip per catalog rule |

Confidence MAY increase slightly for multiple mentions (capped) or matches on lines containing `Skills:`, `Technologies:`, or `Stack:`.

**Ambiguous token rules:**
- `Java` MUST NOT match `JavaScript` — match longer phrases first; use word boundaries
- `Go`, `R` — excluded from MVP catalog (too noisy)
- `AI` — require word boundary; optional context rule in catalog

**Rationale:** Skill identification is entity recognition against a known taxonomy, not corpus statistics. A JSON catalog + regex is deterministic, testable, editable without code changes, and produces explainable `matched_skills` / `missing_skills` output.

**Alternative considered:** TF-IDF — rejected for v1; measures term distinctiveness, not skill presence, and is less explainable for gap analysis.

### 8. Skill matching: weighted keyword overlap

Reuse `extract_skills()` output from the shared extractor. Compare resume skill set against job skill set using weight tiers from `skills.json`.

Fit score formula (0–100):
- For each skill detected in the job, if present in resume → add skill weight to matched score
- Normalize: `fit_score = (matched_weight / total_job_weight) * 100`, capped at 100
- `missing_skills` = job skills not in resume, sorted by weight descending
- Parent/child skills (e.g. `AWS` vs `AWS Lambda`) MUST NOT double-count weight in fit score

**Rationale:** Fit scoring builds on the same catalog and extractor as resume parsing — one source of truth for skills across the pipeline.

### 9. Career track classification: keyword scoring

Each track has a keyword list. Score = count of keyword hits in job title + description (case-insensitive). `track_scores` = dict of track → score. `primary_track` = highest-scoring track (ties broken by predefined priority order).

Jobs can belong to multiple tracks (all tracks with score > 0).

### 10. Seniority estimation: title-first keyword rules

Check job title for seniority keywords in priority order (manager > principal > staff > lead > senior > mid > junior). Fall back to description if title is ambiguous. Default: `unknown`.

### 11. Data persistence: local filesystem only

- Uploads: `data/uploads/{timestamp}_{filename}`
- Extracted text: `data/processed/resume_text.txt`
- Raw API responses (optional): `data/raw/{source}_{timestamp}.json`
- Reports: `reports/job_matches.csv`, `reports/market_summary.md`, `reports/market_fit_report.pdf`

No database. Each analysis run overwrites previous reports.

### 12. Web layer: FastAPI + Jinja2Templates

- `GET /` — render upload form
- `POST /analyze` — multipart form: PDF file, max_results, source selector, optional Adzuna country; pass `pdf_generated` flag to results template
- `GET /download/job_matches.csv`, `GET /download/market_summary.md`, and `GET /download/market_fit_report.pdf` — FileResponse or friendly 404
- PDF endpoint returns `Content-Disposition: inline` for in-browser viewing
- Static CSS at `web/static/styles.css`

Form validation: reject non-PDF uploads with error message; handle empty/unreadable PDFs gracefully.

**Auto-open PDF (Option A):** When `pdf_generated` is true, `results.html` includes a minimal inline script:

```javascript
var pdf = window.open('/download/market_fit_report.pdf', '_blank', 'noopener');
if (!pdf) { /* show popup-blocked fallback link */ }
```

No frontend framework. Results page stays in the current tab; PDF opens in a new tab. If the browser blocks the popup, a prominent manual "Open PDF report" link is shown. No auto-open when PDF was not generated.

### 13. Configuration: `python-dotenv` + `config.py`

Load `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` from `.env`. Adzuna collector checks credentials at call time; if missing, returns empty list + warning string.

Load `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` from `.env`. Adzuna collector checks credentials at call time; if missing, returns empty list + warning string.

Also load optional Ollama settings: `OLLAMA_BASE_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3.2`). If Ollama is unreachable, PDF generation falls back to a deterministic template executive summary.

### 15. Summary PDF with local LLM narrative

Generate a single consolidated summary PDF at `reports/market_fit_report.pdf` containing the most important analysis results. PDF layout uses `fpdf2`; executive summary narrative uses a local Ollama instance via HTTP.

**Pipeline:**

```
JobMatch[] (all analyzed)
        │
        ▼
filter top 20 by fit_score          ← only profile-relevant jobs for LLM + PDF highlights
        │
        ▼
build ReportSummaryContext          ← structured Pydantic model, no raw text fields
        │
        ├──▶ market_summary.md      (deterministic, all jobs)
        ├──▶ job_matches.csv        (deterministic, all jobs)
        │
        └──▶ Ollama HTTP API         ← executive summary narrative ONLY
                 │                      input: ReportSummaryContext JSON
                 │                      output: 2–3 paragraph prose
                 ▼
             fpdf2 PDF layout        ← deterministic tables + LLM narrative + recommendation
                 │
                 ▼
             market_fit_report.pdf
```

**ReportSummaryContext (LLM input — structured only):**

| Field | Source | Included |
|---|---|---|
| `resume_skills` | DetectedSkill canonical names | ✅ |
| `total_jobs_analyzed` | count | ✅ |
| `jobs_by_source` | aggregated counts + avg fit | ✅ |
| `jobs_by_track` | aggregated counts + avg fit | ✅ |
| `top_requested_skills` | top 20 skill names + frequency | ✅ |
| `top_missing_skills` | top 20 skill names + frequency | ✅ |
| `top_matching_jobs` | top 20 by fit: title, company, source, fit_score, primary_track, matched_skills, missing_skills, seniority, url | ✅ |
| `study_recommendation` | pre-computed deterministic text | ✅ |
| `per_source_summary` | compact stats per platform | ✅ |
| Job description text | — | ❌ never |
| Resume raw text | — | ❌ never |
| Jobs below top 20 fit | — | ❌ not sent to LLM |

**LLM constraints:**
- Receives only `ReportSummaryContext` serialized as JSON in the prompt
- Task: write an executive summary (2–3 paragraphs) interpreting the structured findings
- MUST NOT invent skills, job counts, fit scores, or recommendations not present in the input
- If Ollama fails or is unavailable: use deterministic template executive summary (same metrics, no prose generation)

**PDF sections (summary only, not full job table):**
1. Title and analysis date
2. Executive summary (LLM narrative or template fallback)
3. Resume skills detected
4. Market overview — jobs by track, jobs by source
5. Top missing skills
6. Per-source snapshot (count, avg fit, top track)
7. Top 20 matching jobs table (metadata only, no descriptions)
8. Study recommendation (deterministic, pre-computed)

Full job data remains in CSV only.

**Rationale:** LLM adds readable narrative without compromising determinism of matching. Restricting input to structured, pre-filtered data prevents hallucination from raw job text and keeps privacy boundaries clear.

**Alternative considered:** Fully deterministic PDF — rejected; user wants LLM narrative for executive summary readability.

**Alternative considered:** Cloud LLM — rejected; local Ollama keeps data on-machine and avoids API keys.

### 17. Job source authentication and API setup

Each job platform has different auth requirements and usage terms. The app MUST work with zero API keys using Remotive and Arbeitnow alone.

**Remotive — no authentication**

| | |
|---|---|
| **Endpoint** | `GET https://remotive.com/api/remote-jobs` |
| **Auth** | None |
| **Setup** | No configuration required |
| **Optional params** | `category`, `search`, `limit`, `company_name` |
| **MVP strategy** | One batch call with `category=software-dev`; client-side keyword filtering for 13 default queries |
| **Rate limit** | ~4 API calls/day recommended by Remotive — batch fetch keeps to 1 call per analysis |
| **Data delay** | Jobs delayed 24 hours on public API |
| **Attribution** | MUST mention Remotive as source; job links MUST point to Remotive URLs; display attribution on results page and in reports |

**Adzuna — free developer registration required**

| | |
|---|---|
| **Endpoint** | `GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}` |
| **Auth** | `app_id` + `app_key` as query parameters on every request |
| **Setup** | Register at [developer.adzuna.com](https://developer.adzuna.com/) → create application → copy App ID and App Key → add to `.env` as `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` |
| **If missing** | Skip Adzuna collection; show friendly warning; Remotive + Arbeitnow continue |
| **Countries** | `gb`, `us`, `es`, `de`, `nl`, `ie` (in URL path) |
| **Optional params** | `what`, `where`, `results_per_page`, `salary_min`, `full_time`, etc. |

**Arbeitnow — no authentication (free public API)**

| | |
|---|---|
| **Endpoint** | `GET https://www.arbeitnow.com/api/job-board-api` |
| **Auth** | None for free tier |
| **Setup** | No configuration required |
| **Optional params** | `visa_sponsorship`, pagination (`page`) |
| **MVP strategy** | Paginated fetch; client-side keyword filtering; use `remote` field when filtering for remote roles |
| **Notes** | European-focused; jobs sourced from ATS platforms (Greenhouse, SmartRecruiters, etc.); paid custom API exists for high volume — not needed for MVP |

**Minimum setup (no `.env` keys):**

```
pip install → uvicorn → works with Remotive + Arbeitnow
```

**Full setup:**

```env
ADZUNA_APP_ID=your_app_id       # from developer.adzuna.com
ADZUNA_APP_KEY=your_app_key
OLLAMA_BASE_URL=http://localhost:11434   # optional
OLLAMA_MODEL=llama3.2                    # optional
```

### 18. Testing strategy: pytest mapped to spec scenarios

Comprehensive test coverage across all capabilities. Every spec scenario maps to at least one pytest test function. No live external calls in tests.

**Tools:**
- **pytest** — test runner
- **pytest-mock** — mock patching (`mocker` fixture)
- **FastAPI TestClient** — web route tests (from `fastapi.testclient`, uses httpx)
- **tmp_path** — isolated `data/` and `reports/` directories per test
- **Fixtures** — `tests/conftest.py` + `tests/fixtures/` (sample PDF, API JSON payloads)

**Test pyramid:**

```
tests/
  conftest.py                      ← shared fixtures, TestClient, tmp dirs
  fixtures/
    sample_resume.pdf
    remotive_response.json
    adzuna_response.json
    arbeitnow_response.json
  test_resume_parser.py            ← resume-parsing spec
  test_skill_extractor.py          ← resume-parsing spec
  test_collectors.py               ← job-collection spec (per-source normalization)
  test_orchestrator.py             ← job-collection spec (multi-source, fault tolerance)
  test_normalizer.py               ← job-collection spec (deduplication)
  test_track_classifier.py         ← job-matching spec
  test_matcher.py                  ← job-matching spec
  test_aggregator.py               ← job-matching spec (top skills ranking)
  test_report_context.py           ← report-generation spec
  test_report_csv.py               ← report-generation spec
  test_report_markdown.py          ← report-generation spec
  test_llm_summarizer.py           ← report-generation spec (structured input only)
  test_report_pdf.py               ← report-generation spec
  test_web_app.py                  ← web-app spec (all routes, warnings, downloads)
  test_integration_pipeline.py     ← full POST /analyze flow, all mocked
  test_models.py                   ← Pydantic model validation
```

**Rules:**
- Mock all Remotive, Adzuna, Arbeitnow, and Ollama HTTP with fixture JSON — never call live APIs in CI or local test runs
- Verify LLM prompt payload contains only `ReportSummaryContext` JSON — assert no job description or resume text fields
- Use `WHEN/THEN` from specs as test function docstrings for traceability
- Web tests use TestClient; no browser automation needed for MVP
- Integration test mocks entire pipeline externals but exercises real orchestration code path

**Priority order if time-constrained:**
1. Must have: skill extractor, matcher, collectors normalization, web `/analyze` happy path + error cases
2. Should have: report generation, LLM summarizer, orchestrator fault tolerance
3. Nice to have: integration pipeline, models validation, PDF content assertions

**Configuration:** `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml`; document `pytest` command in README.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| PDF text extraction quality varies (scanned PDFs) | Graceful error message; save whatever text is extracted; document limitation in README |
| Job API rate limits or downtime | Per-source try/except; continue with remaining sources; show warnings in UI; Remotive uses single batch fetch (1 call/run) |
| Adzuna requires credentials | Skip gracefully with friendly warning; Remotive + Arbeitnow remain functional; document registration steps in README |
| Remotive rate limit exceeded | Single batch API call per analysis with client-side filtering; never call Remotive once per default query |
| Remotive attribution required | Display "Jobs from Remotive" with link on results page; include source attribution in reports; job links use Remotive URLs |
| Keyword matching produces false positives/negatives | Word-boundary regex, alias rules, and ambiguous-token exclusions in `skills.json`; document remaining limitations in README |
| Duplicate jobs across sources/queries | Deduplicate by URL or (title, company) before analysis |
| Large result sets slow the UI | Default max_results=100; cap per-source budget; paginate table optionally in future |
| Incomplete salary/location data from APIs | Nullable fields in `JobPosting`; display "N/A" in UI |
| Analysis overwrites previous reports | Acceptable for single-user local MVP; document behavior |
| LLM hallucinates skills or metrics not in structured input | Strict prompt constraints; LLM receives only pre-computed JSON; deterministic sections (tables, recommendation) bypass LLM |
| Ollama not installed or unreachable | Fall back to template executive summary; PDF still generated; show friendly warning on results page |
| Browser blocks PDF popup on results page | Show prominent manual "Open PDF report" fallback link; document popup blocker behavior in README |

## Migration Plan

Not applicable — greenfield project. Setup steps:

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`
3. **Optional — Adzuna:** Register at [developer.adzuna.com](https://developer.adzuna.com/), create an application, add `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` to `.env`
4. **Optional — Ollama:** Install Ollama, run `ollama pull llama3.2` for LLM executive summary in PDF
5. `uvicorn src.app:app --reload`
6. Open `http://localhost:8000`

The app runs immediately after step 5 with Remotive and Arbeitnow — no API keys required.

## Open Questions

- **Deduplication strategy:** Prefer URL-based dedup; fall back to normalized (title, company) if URL missing. Resolve during implementation.
- **Per-query result budget:** Split max_results evenly across default queries, or cap per query (e.g., 10)? Recommend cap-per-query to avoid one query consuming the entire budget.
- **Arbeitnow pagination:** Confirm pagination parameter and response schema during implementation (`GET https://www.arbeitnow.com/api/job-board-api`).
