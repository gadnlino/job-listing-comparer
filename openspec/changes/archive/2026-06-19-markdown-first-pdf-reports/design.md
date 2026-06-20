## Context

The career-market-fit-scanner MVP generates three report artifacts after analysis:

- `job_matches.csv` — full data export
- `market_summary.md` — rich Markdown (bullets, all sections)
- `market_fit_report.pdf` — sparse fpdf2 layout (subset of sections, poor formatting)

These are built by separate functions in `report_generator.py`, causing content drift. Manual fpdf2 calls (`cell`, `multi_cell`) are error-prone (cursor positioning bugs, no real tables) and cannot reliably meet the spec's PDF section requirements.

The user requires **reliably well-formatted** PDF output. The agreed approach is Markdown as the single authoring format, with PDF as a rendered view of that document.

## Goals / Non-Goals

**Goals:**

- One canonical Markdown builder used for both Markdown download and PDF generation
- PDF with proper headings, spacing, bullet lists, and HTML tables for top jobs and market overview
- All spec-required PDF sections present and matching Markdown content
- Graceful error when WeasyPrint system libraries are missing (clear message, CSV still works)
- Tests cover Markdown structure and PDF render path (mocked externals)

**Non-Goals:**

- Changing LLM scope, Ollama integration, or `ReportSummaryContext` shape
- Changing CSV format or job matching logic
- Pandoc or LaTeX as PDF engine (adds external binary dependency)
- Custom PDF styling beyond a single CSS stylesheet
- WYSIWYG or user-editable report templates

## Decisions

### 1. Canonical report file: `market_fit_report.md`

Write one print-ready Markdown file to `reports/market_fit_report.md`. Both the Markdown download endpoint and PDF renderer read/write this file.

**Rationale:** Single source of truth; filename aligns with PDF (`market_fit_report.pdf`).

**Alternative considered:** Keep `market_summary.md` as analysis export and separate `market_fit_report.md` — rejected; duplicates content.

### 2. PDF renderer: Markdown → HTML → WeasyPrint

Pipeline:

```
ReportSummaryContext + executive_summary
        │
        ▼
build_report_markdown()          ← single function, all sections
        │
        ├──▶ reports/market_fit_report.md
        │
        └──▶ render_pdf_from_markdown()
                 │
                 ├── markdown library → HTML fragment
                 ├── Jinja2 wrapper (report.html) + CSS (report.css)
                 └── WeasyPrint HTML().write_pdf()
                          │
                          ▼
                 reports/market_fit_report.pdf
```

**Rationale:** WeasyPrint gives reliable formatting via CSS (tables, page breaks, typography) while staying in the Python ecosystem. CSS is easier to maintain than fpdf2 imperative layout.

**Alternatives considered:**
- **Pandoc** — excellent output but external binary; worse zero-config story
- **fpdf2 tables** — stays in current stack but doesn't solve "write once" architecture
- **fpdf2 write_html()** — limited HTML/CSS support

### 3. Markdown content structure: print-ready with GFM tables

The canonical Markdown SHALL include:

1. `# Career Market Fit Report` + generated date
2. `## Executive Summary` — LLM or template text
3. `## Resume Skills Detected` — comma-separated or bullet list
4. `## Market Overview` — jobs by source and by track as Markdown tables
5. `## Top Missing Skills` — ranked list with counts
6. `## Per-Source Snapshot` — table: source, count, avg fit, top track
7. `## Top 20 Matching Jobs` — GFM table with title, company, source, fit, track, seniority, url
8. `## Study Recommendation` — deterministic text
9. Footer attribution for Remotive / other sources

**Rationale:** GFM tables render cleanly through `markdown` library with `tables` extension into HTML tables that WeasyPrint handles well.

### 4. HTML wrapper and CSS

- `src/analysis/templates/report.html` — minimal HTML shell: `<html>`, `<head>` linking CSS, `<body>{{ content }}`
- `src/analysis/templates/report.css` — print-oriented styles: font stack, heading hierarchy, table borders, page margins, `@page` size A4, `word-break` for long URLs

Use Jinja2 (already a project dependency via FastAPI) to wrap the converted HTML body.

**Rationale:** Separates content (Markdown) from presentation (CSS); CSS changes don't require Python changes.

### 5. Remove fpdf2

Delete `write_summary_pdf()` and remove `fpdf2` from `requirements.txt` after migration.

**Rationale:** No remaining use case once PDF comes from WeasyPrint.

### 6. WeasyPrint unavailable: fail PDF with clear warning, keep Markdown

If WeasyPrint import fails or `write_pdf()` raises (missing system libs):

- Still write `market_fit_report.md`
- Skip PDF generation (`pdf_generated=False`)
- Add warning string to analysis result: `"PDF generation unavailable — install WeasyPrint system dependencies (see README)"`
- Results page shows existing no-PDF / warning behavior

**Rationale:** App remains usable on machines without Cairo/Pango; Markdown download still delivers full report.

**Alternative considered:** Fallback to fpdf2 — rejected; defeats formatting goal.

### 7. Download endpoint compatibility

`GET /download/market_summary.md` continues to work but serves `reports/market_fit_report.md` content (same canonical file). Optionally add `GET /download/market_fit_report.md` alias.

**Rationale:** Avoid breaking bookmarked URLs while consolidating on-disk artifact.

### 8. Testing strategy

- **Unit:** `build_report_markdown()` — assert all required sections, table syntax, top 20 rows, no raw job descriptions
- **Unit:** `render_pdf_from_markdown()` — mock `weasyprint.HTML.write_pdf`, assert called with HTML containing expected headings
- **Integration:** existing pipeline tests mock WeasyPrint; assert both `.md` and `.pdf` paths written when mock succeeds
- **Optional:** `@pytest.mark.skipif(not weasyprint_available)` for one smoke test on dev machines with libs installed

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| WeasyPrint system deps hard to install on some machines | Document brew install; graceful skip with warning; Markdown still available |
| LLM summary contains Markdown syntax that breaks layout | Accept as feature; CSS handles headings/lists; sanitize only if issues arise |
| Long URLs overflow table cells | CSS `word-break: break-all` on URL column |
| WeasyPrint slower than fpdf2 | Acceptable for local single-user analysis (~1–2s) |
| CI lacks WeasyPrint libs | Mock in all CI tests; optional real render test marked skipif |

## Migration Plan

1. Implement new pipeline alongside old (feature flag or parallel functions)
2. Verify PDF output manually against spec sections
3. Remove fpdf2 code and dependency
4. Update README and `.env.example` (no new env vars needed)
5. Run full pytest suite

No database migration. Reports directory overwritten on each analysis as today.

## Open Questions

- _(none — renderer choice and file naming decided)_
