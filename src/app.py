import threading
from queue import Queue
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.analysis.pipeline import AnalysisInputError, AnalysisView, run_analysis
from src.analysis.progress import QueueProgressReporter, done_event, error_event, format_ndjson_line
from src.config import (
    DEFAULT_ADZUNA_COUNTRIES,
    PROCESSED_DIR,
    REPORTS_DIR,
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOADS_DIR,
)

app = FastAPI(title="Career Market Fit Scanner")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_last_analysis_view: AnalysisView | None = None


def _set_analysis_view(view: AnalysisView) -> None:
    global _last_analysis_view
    _last_analysis_view = view


def _resolve_sources(source: str) -> list[str]:
    if source == "all":
        return ["remotive", "adzuna", "arbeitnow"]
    return [source]


def _resolve_countries(country: str) -> list[str]:
    if country == "all":
        return DEFAULT_ADZUNA_COUNTRIES
    return [country]


def _render_results(request: Request, view: AnalysisView):
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "result": view.result,
            "pdf_generated": view.pdf_generated,
            "llm_fallback": view.llm_fallback,
            "has_remotive": view.has_remotive,
        },
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"adzuna_countries": DEFAULT_ADZUNA_COUNTRIES},
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    max_results: int = Form(100),
    source: str = Form("all"),
    adzuna_country: str = Form("all"),
):
    content = await file.read()
    try:
        view = run_analysis(
            content,
            file.filename or "",
            max_results,
            _resolve_sources(source),
            _resolve_countries(adzuna_country),
        )
    except AnalysisInputError as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": str(exc), "adzuna_countries": DEFAULT_ADZUNA_COUNTRIES},
            status_code=400,
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "error": f"Analysis failed: {exc}",
                "adzuna_countries": DEFAULT_ADZUNA_COUNTRIES,
            },
            status_code=500,
        )

    return _render_results(request, view)


@app.post("/analyze/stream")
async def analyze_stream(
    file: UploadFile = File(...),
    max_results: int = Form(100),
    source: str = Form("all"),
    adzuna_country: str = Form("all"),
):
    content = await file.read()
    filename = file.filename or ""

    def generate():
        queue: Queue[str | None] = Queue()
        holder: dict[str, AnalysisView] = {}
        error_holder: dict[str, str] = {}

        def worker():
            try:
                reporter = QueueProgressReporter(queue)
                holder["view"] = run_analysis(
                    content,
                    filename,
                    max_results,
                    _resolve_sources(source),
                    _resolve_countries(adzuna_country),
                    reporter=reporter,
                )
            except AnalysisInputError as exc:
                error_holder["message"] = str(exc)
            except Exception as exc:
                error_holder["message"] = f"Analysis failed: {exc}"
            finally:
                queue.put(None)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        while True:
            line = queue.get()
            if line is None:
                break
            yield line

        thread.join()

        if "message" in error_holder:
            yield format_ndjson_line(error_event(error_holder["message"]))
            return

        _set_analysis_view(holder["view"])
        yield format_ndjson_line(done_event("/analyze/result"))

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/analyze/result", response_class=HTMLResponse)
async def analyze_result(request: Request):
    if _last_analysis_view is None:
        return RedirectResponse("/", status_code=303)
    return _render_results(request, _last_analysis_view)


def _download_file(path, filename: str, inline: bool = False) -> FileResponse | HTMLResponse:
    if not path.exists():
        return HTMLResponse(
            f"<h1>Report not available</h1><p>{filename} has not been generated yet.</p>",
            status_code=404,
        )
    headers = {}
    if inline:
        headers["Content-Disposition"] = f'inline; filename="{filename}"'
    else:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    media = "application/pdf" if filename.endswith(".pdf") else None
    return FileResponse(path, filename=filename, headers=headers, media_type=media)


@app.get("/download/job_matches.csv")
async def download_csv():
    return _download_file(REPORTS_DIR / "job_matches.csv", "job_matches.csv")


@app.get("/download/market_summary.md")
async def download_markdown():
    return _download_file(REPORTS_DIR / "market_fit_report.md", "market_summary.md")


@app.get("/download/market_fit_report.pdf")
async def download_pdf():
    return _download_file(
        REPORTS_DIR / "market_fit_report.pdf",
        "market_fit_report.pdf",
        inline=True,
    )
