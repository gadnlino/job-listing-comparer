import re
from pathlib import Path
import os
import sys

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

PDF_UNAVAILABLE_MSG = (
    "PDF generation unavailable — install WeasyPrint system dependencies with: "
    "brew install glib pango cairo gdk-pixbuf libffi (see README)."
)

_HOMEBREW_LIB_DIRS = (
    Path("/opt/homebrew/lib"),  # Apple Silicon
    Path("/usr/local/lib"),     # Intel macOS / older Homebrew
)


def _configure_weasyprint_library_path() -> None:
    """Help WeasyPrint find Homebrew-provided Pango/Cairo/GLib on macOS."""
    if sys.platform != "darwin":
        return

    candidates = [
        path for path in _HOMEBREW_LIB_DIRS
        if (path / "libgobject-2.0.0.dylib").exists() or (path / "libgobject-2.0.dylib").exists()
    ]
    if not candidates:
        return

    prefix = ":".join(str(path) for path in candidates)
    existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if existing:
        if prefix not in existing:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{prefix}:{existing}"
    else:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = prefix


def _import_weasyprint_html():
    _configure_weasyprint_library_path()
    from weasyprint import HTML

    return HTML


def _prepare_html_for_pdf(html_body: str) -> str:
    """Tag tables for print layout; mark wide job tables so URLs wrap inside the page."""
    table_pattern = re.compile(r"<table>.*?</table>", re.DOTALL)

    def tag_table(match: re.Match[str]) -> str:
        table_html = match.group(0)
        col_count = table_html.count("<th>")
        if col_count >= 7:
            return table_html.replace("<table>", '<table class="wide-table">', 1)
        return table_html

    return table_pattern.sub(tag_table, html_body)


def render_pdf_from_markdown(md_path: Path, pdf_path: Path) -> tuple[Path | None, str | None]:
    try:
        HTML = _import_weasyprint_html()
    except (ImportError, OSError):
        return None, PDF_UNAVAILABLE_MSG

    try:
        md_text = md_path.read_text(encoding="utf-8")
        html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
        html_body = _prepare_html_for_pdf(html_body)
        styles = (TEMPLATES_DIR / "report.css").read_text(encoding="utf-8")
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("report.html")
        html_full = template.render(content=html_body, styles=styles)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html_full, base_url=str(TEMPLATES_DIR)).write_pdf(str(pdf_path))
        return pdf_path, None
    except Exception as exc:
        return None, f"PDF generation unavailable — {exc}"
