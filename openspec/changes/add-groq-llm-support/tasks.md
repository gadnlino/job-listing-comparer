## 1. Configuration

- [x] 1.1 Add `LLM_API_KEY` to `src/config.py` (read from env, strip whitespace, default empty)
- [x] 1.2 Add `PDF_RENDERER` to `src/config.py` (`browser` | `weasyprint` | `off`; default `weasyprint` for local backward compatibility)
- [x] 1.3 Create or update `.env.example` with Groq vars, `PDF_RENDERER`, Railway profile comments, and optional link-validation tuning

## 2. LLM summarizer (Groq)

- [x] 2.1 Update `generate_llm_summary()` to pass `Authorization: Bearer` when `LLM_API_KEY` is set
- [x] 2.2 Keep OpenAI-compatible → Ollama → template fallback chain unchanged

## 3. Report HTML builder and PDF modes

- [x] 3.1 Extract `build_report_html(md_path)` from `pdf_renderer.py` (Markdown → HTML + `report.css` wrapper)
- [x] 3.2 Update `render_pdf_from_markdown()` to use shared HTML builder (weasyprint path only when `PDF_RENDERER=weasyprint`)
- [x] 3.3 Update `generate_reports()` / pipeline: skip server PDF when `PDF_RENDERER=browser` or `off`; set `pdf_generated=True` when printable report available in browser/weasyprint modes
- [x] 3.4 Add `GET /report/print` route serving printable HTML from current `market_fit_report.md` (404-friendly when missing)

## 4. Browser PDF auto-download

- [x] 4.1 Add print page template with inline `report.css` and html2pdf.js (or equivalent client library)
- [x] 4.2 On page load, auto-run client PDF generation and download `market_fit_report.pdf` (no in-app button)
- [x] 4.3 Update `results.html`: auto-open `/report/print` when `PDF_RENDERER=browser`; keep `/download/market_fit_report.pdf` auto-open for weasyprint mode; update manual fallback links

## 5. Dependencies and Docker

- [x] 5.1 Remove unused `pandas` from `requirements.txt`
- [x] 5.2 Document slim Docker / browser-only deploy (WeasyPrint apt packages optional when not using weasyprint mode)
- [x] 5.3 Stop copying unnecessary paths into production image if applicable (e.g. `openspec/`)

## 6. Tests

- [x] 6.1 LLM tests: Groq-style response, Authorization header present/absent
- [x] 6.2 HTML builder tests: required sections in output
- [x] 6.3 `PDF_RENDERER=browser`: no server PDF write, `pdf_generated=True`, `/report/print` returns HTML with download script
- [x] 6.4 `PDF_RENDERER=weasyprint`: existing PDF tests still pass (WeasyPrint mocked)
- [x] 6.5 Web app tests: results page auto-open script per renderer mode

## 7. Documentation

- [x] 7.1 README: Groq setup (console.groq.com, free tier, privacy note)
- [x] 7.2 README: `PDF_RENDERER` modes (browser vs weasyprint vs off)
- [x] 7.3 README: Railway free-tier deploy profile (Groq + browser PDF, app-only, env tuning, no llama sidecar)
- [x] 7.4 Update LLM fallback warning copy to generic "LLM" wording

## 8. Verification

- [x] 8.1 Run `pytest` — all tests pass without live Groq/Ollama/WeasyPrint
- [ ] 8.2 Manual smoke: `PDF_RENDERER=browser` — analyze, verify auto-open tab and PDF download
- [ ] 8.3 Manual smoke (optional): Groq key + browser mode together
