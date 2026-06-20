## 1. Dependencies and Templates

- [x] 1.1 Add `weasyprint` and `markdown` to `requirements.txt`; remove `fpdf2`
- [x] 1.2 Create `src/analysis/templates/report.html` — HTML shell wrapping converted Markdown body
- [x] 1.3 Create `src/analysis/templates/report.css` — print styles (A4 `@page`, headings, tables, URL word-break, margins)

## 2. Canonical Markdown Builder

- [x] 2.1 Implement `build_report_markdown(context, executive_summary, generated_at)` — single function with all spec sections
- [x] 2.2 Include GFM tables for jobs by source, jobs by track, per-source snapshot, and top 20 matching jobs
- [x] 2.3 Include title, generated date, resume skills, top requested/missing skills, study recommendation, and source attribution footer
- [x] 2.4 Replace `write_market_summary_md()` with write to `reports/market_fit_report.md` using the canonical builder

## 3. PDF Renderer

- [x] 3.1 Implement `src/analysis/pdf_renderer.py` with `render_pdf_from_markdown(md_path, pdf_path)` — Markdown → HTML (tables extension) → Jinja wrapper → WeasyPrint
- [x] 3.2 Handle WeasyPrint import/runtime failure — return `(pdf_path=None, warning=str)` without crashing analysis
- [x] 3.3 Remove `write_summary_pdf()` and all fpdf2 imports from `report_generator.py`

## 4. Pipeline Integration

- [x] 4.1 Refactor `generate_reports()` — build Markdown first, write `.md`, then render PDF from same content
- [x] 4.2 Update `src/app.py` to surface WeasyPrint-unavailable warning in `collection.warnings` or analysis warnings when PDF skipped
- [x] 4.3 Update `GET /download/market_summary.md` to serve `reports/market_fit_report.md`

## 5. Tests

- [x] 5.1 Refactor `tests/test_report_markdown.py` — assert all sections, GFM tables, top 20 filter, no raw descriptions
- [x] 5.2 Refactor `tests/test_report_pdf.py` — mock WeasyPrint; test multi-job render; test graceful skip on failure
- [x] 5.3 Update `tests/test_integration_pipeline.py` — assert `market_fit_report.md` and `.pdf` paths
- [x] 5.4 Update `tests/test_web_app.py` if warning messages or file paths change
- [x] 5.5 Run full `pytest` suite and fix failures

## 6. Documentation and Manual Verification

- [x] 6.1 Update `README.md` — WeasyPrint setup (`brew install pango cairo gdk-pixbuf libffi`), note `market_fit_report.md` as canonical report, remove fpdf2 references
- [ ] 6.2 Manual verification — run analysis with WeasyPrint installed; confirm PDF has formatted tables and matches Markdown content
