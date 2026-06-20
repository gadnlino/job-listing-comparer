## 1. Project Scaffolding

- [x] 1.1 Create directory structure: `src/`, `src/resume/`, `src/collectors/`, `src/analysis/`, `src/web/templates/`, `src/web/static/`, `data/uploads/`, `data/raw/`, `data/processed/`, `reports/`, `tests/`, `tests/fixtures/`
- [x] 1.2 Create `requirements.txt` with FastAPI, Uvicorn, Jinja2, python-multipart, httpx, pydantic, pandas, pypdf, fpdf2, python-dotenv, pytest, pytest-mock
- [x] 1.3 Create `.env.example` with `ADZUNA_APP_ID=`, `ADZUNA_APP_KEY=`, `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.2`
- [x] 1.4 Create `src/config.py` loading environment variables via python-dotenv
- [x] 1.5 Create `src/models.py` with Pydantic models `JobPosting`, `JobMatch`, `DetectedSkill`, and `ReportSummaryContext` (structured LLM input — no raw text fields)
- [x] 1.6 Add `.gitignore` entries for `data/uploads/`, `data/raw/`, `data/processed/`, `reports/`, `.env`
- [x] 1.7 Add `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml`

## 2. Resume Parsing and Skill Catalog

- [x] 2.1 Create `src/resume/skills.json` — canonical names, aliases, weight tiers (high/medium/low), regex patterns with word boundaries for all MVP skills
- [x] 2.2 Implement `src/resume/parser.py` — extract text from PDF using pypdf, handle invalid/unreadable PDFs gracefully
- [x] 2.3 Save extracted text to `data/processed/resume_text.txt`
- [x] 2.4 Implement `src/resume/skill_extractor.py` — load catalog, normalize text, compile regex patterns, expose `extract_skills(text) -> list[DetectedSkill]`
- [x] 2.5 Implement confidence scoring — canonical (1.0), alias (0.9), parent/child (0.85), section boost for Skills/Technologies/Stack lines
- [x] 2.6 Implement ambiguous token rules — Java vs JavaScript (longer match wins), exclude Go/R, AI word-boundary rule
- [x] 2.7 Implement skill deduplication by canonical name (keep highest confidence)

## 3. Job Collectors

- [x] 3.1 Implement `src/collectors/base.py` — abstract base class with `search_jobs(query, max_results, **kwargs) -> list[JobPosting]`
- [x] 3.2 Implement `src/collectors/remotive.py` — batch fetch from `https://remotive.com/api/remote-jobs` (1 call/run, `category=software-dev`), client-side query filtering, Remotive URL attribution
- [x] 3.3 Implement `src/collectors/adzuna.py` — `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}` with `app_id`/`app_key` query params, credential check, graceful skip when missing
- [x] 3.4 Implement `src/collectors/arbeitnow.py` — paginated fetch from `https://www.arbeitnow.com/api/job-board-api`, client-side query filtering, handle missing fields
- [x] 3.5 Implement job orchestration logic — source-specific fetch strategies, catch per-source errors, collect warnings, deduplicate jobs

## 4. Analysis Engine

- [x] 4.1 Implement `src/analysis/normalizer.py` — shared normalization helpers and deduplication utilities
- [x] 4.2 Implement `src/analysis/track_classifier.py` — classify jobs into 5 career tracks with track_scores and primary_track
- [x] 4.3 Implement `src/analysis/matcher.py` — reuse `extract_skills()` on job title+description, weighted fit score (0–100), matched_skills, missing_skills, parent/child no double-count, seniority estimation
- [x] 4.4 Implement market aggregation helpers — top requested skills, top missing skills, jobs by track/source counts

## 5. Report Generation

- [x] 5.1 Implement `src/analysis/report_generator.py` — generate `reports/job_matches.csv` with required columns sorted by fit_score
- [x] 5.2 Implement market summary generation — `reports/market_summary.md` with all required sections and deterministic study recommendation
- [x] 5.3 Implement `build_report_context()` — aggregate computed metrics into `ReportSummaryContext`, filter top 20 jobs by fit score, exclude all raw text fields
- [x] 5.4 Implement `src/analysis/llm_summarizer.py` — Ollama HTTP client, prompt with structured JSON only, template fallback on failure
- [x] 5.5 Implement summary PDF generation — `reports/market_fit_report.pdf` via fpdf2 with LLM executive summary + deterministic tables and recommendation

## 6. Web Application

- [x] 6.1 Implement `src/app.py` — FastAPI app with Jinja2Templates and static file mounting
- [x] 6.2 Create `src/web/templates/index.html` — upload form with max results, source selector, Adzuna country selector
- [x] 6.3 Create `src/web/templates/results.html` — summary cards, resume skills, track breakdown, top jobs, full sorted table, PDF auto-open script with popup-blocked fallback
- [x] 6.4 Create `src/web/static/styles.css` — simple readable layout
- [x] 6.5 Implement `GET /` — render home page
- [x] 6.6 Implement `POST /analyze` — full pipeline; pass `pdf_generated` flag to results template
- [x] 6.7 Implement download endpoints — PDF returns `Content-Disposition: inline`; CSV/Markdown/PDF FileResponse with friendly error when missing
- [x] 6.8 Display source failure warnings, Adzuna skipped warning, Remotive attribution, LLM fallback warning, and no-jobs-found message on results page

## 7. Documentation and Manual Verification

- [x] 7.1 Write `README.md` — project goal, setup (zero-config with Remotive + Arbeitnow), Adzuna registration steps, Ollama setup, platform auth table, Remotive attribution, API rate limits, `pytest` command, usage workflow, skill catalog and LLM scope, MVP limitations, roadmap
- [ ] 7.2 Manual end-to-end verification: upload PDF, analyze with All sources, verify results page, download CSV, Markdown, and PDF reports
- [ ] 7.3 Manual graceful degradation check: run with no `.env` keys (Remotive + Arbeitnow only); run without Ollama (template PDF fallback)

## 8. Test Suite

- [x] 8.1 Create `tests/conftest.py` and `tests/fixtures/` — sample PDF, Remotive/Adzuna/Arbeitnow JSON payloads, TestClient fixture, isolated tmp data/report dirs
- [x] 8.2 `tests/test_resume_parser.py` — valid PDF, invalid PDF, empty text
- [x] 8.3 `tests/test_skill_extractor.py` — known skills, aliases, JavaScript≠Java, deduplication, confidence tiers, excluded tokens, DetectedSkill shape
- [x] 8.4 `tests/test_collectors.py` — Remotive/Adzuna/Arbeitnow normalization from fixtures; Remotive single-call batch; Adzuna credential skip
- [x] 8.5 `tests/test_orchestrator.py` — multi-source collection, per-source error isolation, zero-config mode, client-side query filtering
- [x] 8.6 `tests/test_normalizer.py` — deduplication by URL and title+company fallback
- [x] 8.7 `tests/test_track_classifier.py` — multi-track assignment, primary track selection
- [x] 8.8 `tests/test_matcher.py` — fit score bounds, weight tiers, parent/child dedup, seniority, shared extractor on job title+description
- [x] 8.9 `tests/test_aggregator.py` — top requested skills and top missing skills ranking
- [x] 8.10 `tests/test_report_context.py` — structured fields only, no descriptions, top 20 filter
- [x] 8.11 `tests/test_report_csv.py` — required columns, fit_score descending sort
- [x] 8.12 `tests/test_report_markdown.py` — all sections, deterministic study recommendation
- [x] 8.13 `tests/test_llm_summarizer.py` — structured JSON prompt only, no raw text, template fallback on Ollama failure
- [x] 8.14 `tests/test_report_pdf.py` — PDF created with sections, skipped when no jobs
- [x] 8.15 `tests/test_web_app.py` — GET /, POST /analyze, download endpoints, PDF inline headers, auto-open script when PDF generated, no auto-open when no jobs, popup-blocked fallback element, warnings, download 404
- [x] 8.16 `tests/test_integration_pipeline.py` — full POST /analyze with all externals mocked, reports written, results rendered
- [x] 8.17 `tests/test_models.py` — Pydantic validation for JobPosting, JobMatch, DetectedSkill, ReportSummaryContext
- [x] 8.18 Run full test suite with `pytest` and fix any failures
