## Why

The summary PDF is generated today with imperative `fpdf2` layout code that duplicates (and diverges from) the Markdown report. This produces poorly formatted PDFs — missing sections, plain-text job lines instead of tables, and fragile layout bugs. Users need a reliably well-formatted PDF that matches the analysis content.

Making Markdown the single source of truth and rendering PDF from it eliminates duplication and ensures consistent structure across downloadable formats.

## What Changes

- Replace direct `fpdf2` PDF layout with a **Markdown-first pipeline**: build one canonical report Markdown file, then render PDF from it.
- Introduce **WeasyPrint** (Markdown → HTML + CSS → PDF) for reliable typography, headings, lists, and tables.
- Consolidate report content into a **print-ready** `reports/market_fit_report.md` with all spec-required sections (title, date, executive summary, market overview, top missing skills, per-source snapshot, top 20 jobs table, study recommendation, attribution).
- Remove `write_summary_pdf()` and the separate sparse fpdf2 code path in `report_generator.py`.
- Remove `fpdf2` from project dependencies (no longer used after this change).
- Add report CSS template at `src/analysis/templates/report.css` and HTML wrapper at `src/analysis/templates/report.html`.
- Update README with WeasyPrint system dependencies (macOS Homebrew packages).
- Update tests to validate canonical Markdown structure and PDF rendering (mock WeasyPrint when system libs unavailable).

**BREAKING:** The Markdown download endpoint `GET /download/market_summary.md` SHALL serve the canonical report file `reports/market_fit_report.md` (same content as the PDF source). The on-disk filename changes from `market_summary.md` to `market_fit_report.md`.

## Capabilities

### New Capabilities

_(none — this change refines existing report generation)_

### Modified Capabilities

- `report-generation`: PDF derived from canonical Markdown via WeasyPrint; single report builder; print-ready sections and tables; remove fpdf2.
- `testing`: Updated report PDF/Markdown tests for new pipeline; WeasyPrint mocking or availability guard.

## Impact

- **Code**: `src/analysis/report_generator.py` (major refactor), new `src/analysis/pdf_renderer.py` (or inline module), new CSS/HTML templates under `src/analysis/templates/`.
- **Dependencies**: Add `weasyprint`, `markdown` (or `markdown-it-py`); remove `fpdf2`.
- **System deps**: macOS requires `brew install pango cairo gdk-pixbuf libffi` for WeasyPrint; document in README.
- **Reports**: `reports/market_fit_report.md` replaces `reports/market_summary.md` as canonical output; `reports/market_fit_report.pdf` rendered from same source.
- **APIs**: Download routes unchanged in URL shape; Markdown download serves new canonical file.
- **LLM / Ollama**: Unchanged — executive summary still generated first, then embedded in canonical Markdown before PDF render.
