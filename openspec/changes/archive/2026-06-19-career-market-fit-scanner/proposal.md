## Why

Backend and cloud developers need a data-driven way to decide which technical specializations are worth investing in next. Job boards are fragmented, and comparing a personal resume against real market demand across multiple platforms is tedious and error-prone. A local tool that aggregates public job APIs, extracts skills from a resume, and ranks career tracks by fit and demand removes guesswork from specialization decisions.

## What Changes

- Introduce a new local web application called **career-market-fit-scanner** built with Python 3.11+, FastAPI, and Jinja2.
- Add resume PDF upload, text extraction, and deterministic skill detection via `skills.json` catalog and regex word-boundary matching (no TF-IDF or NLP; LLM not used for parsing or matching).
- Add job collectors for Remotive (public, no key), Adzuna (optional free developer credentials), and Arbeitnow (public, no key), with source-specific fetch strategies and graceful degradation.
- Add job normalization into a common `JobPosting` model, career track classification, and resume-to-job fit scoring.
- Add a minimal web UI for upload, analysis, and results display (no frontend framework).
- Add CSV, Markdown, and summary PDF report generation with download endpoints.
- Add a local LLM (Ollama) to generate narrative executive summary for the PDF report from structured computed data only — never raw job descriptions or resume text.
- Add comprehensive pytest test suite mapped to all spec scenarios, with mocked external HTTP (no live API calls in tests).
- Add README, `.env.example`, and project scaffolding under the repo root.

## Capabilities

### New Capabilities

- `resume-parsing`: PDF upload, text extraction, and deterministic skill detection from resume content using `skills.json` + regex.
- `job-collection`: Multi-source job API collectors (Remotive, Adzuna, Arbeitnow) with normalization and fault tolerance.
- `job-matching`: Shared skill extractor for jobs, career track classification, weighted fit scoring, seniority estimation, and missing-skill analysis.
- `web-app`: Local FastAPI HTTP server with upload form, analysis endpoint, results page, and download routes.
- `report-generation`: CSV, Markdown, and summary PDF report generation; local LLM narrative for PDF executive summary from structured data only.
- `testing`: Comprehensive pytest suite covering all capabilities with mocked externals; every spec scenario maps to a test case.

### Modified Capabilities

_(none — greenfield project)_

## Impact

- **New codebase**: Full project scaffold under repo root (`src/`, `tests/`, `data/`, `reports/`, `web/`).
- **Skill catalog**: `src/resume/skills.json` — canonical names, aliases, weight tiers, regex patterns; shared by resume parsing and job matching.
- **Dependencies**: FastAPI, Uvicorn, Jinja2, python-multipart, httpx, pydantic, pandas, pypdf, fpdf2, python-dotenv, pytest, pytest-mock (stdlib `re` for skill matching; Ollama via HTTP for PDF narrative only).
- **External APIs**: Remotive public API (no auth), Adzuna Job Search API (free registration, optional), Arbeitnow public API (no auth), Ollama local HTTP API (optional, for PDF executive summary).
- **Environment**: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` optional (register at developer.adzuna.com); `OLLAMA_BASE_URL`, `OLLAMA_MODEL` optional — app runs with zero keys using Remotive + Arbeitnow.
- **Storage**: Local filesystem only (uploads, raw/processed data, reports) — no database.
- **Non-goals for MVP**: No LinkedIn, no scraping, no cloud LLM APIs, no LLM for skill extraction or job matching, no embeddings, no TF-IDF, no NLP libraries, no auth, no deployment, no background workers, no frontend framework.
