from pathlib import Path
import os
import sys
from unittest.mock import MagicMock, patch

from src.analysis.matcher import match_job
from src.analysis.pdf_renderer import (
    PDF_UNAVAILABLE_MSG,
    _configure_weasyprint_library_path,
    render_pdf_from_markdown,
)
from src.analysis.report_context import build_report_context
from src.analysis.report_generator import write_report_markdown
from src.models import JobPosting, ReportSummaryContext, TopJobSummary
from src.resume.skill_extractor import extract_skills
from tests.conftest import mock_pdf_render


def test_configures_homebrew_library_path_on_macos(monkeypatch, tmp_path: Path):
    if sys.platform != "darwin":
        return

    fake_lib = tmp_path / "lib"
    fake_lib.mkdir()
    (fake_lib / "libgobject-2.0.0.dylib").write_bytes(b"")
    monkeypatch.delenv("DYLD_FALLBACK_LIBRARY_PATH", raising=False)

    with patch("src.analysis.pdf_renderer._HOMEBREW_LIB_DIRS", (fake_lib,)):
        _configure_weasyprint_library_path()

    assert os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "").startswith(str(fake_lib))


def test_prepare_html_tags_wide_job_table():
    from src.analysis.pdf_renderer import _prepare_html_for_pdf

    html = (
        "<table><thead><tr>"
        "<th>Title</th><th>Company</th><th>Source</th><th>Fit</th>"
        "<th>Track</th><th>Seniority</th><th>Link Status</th><th>URL</th>"
        "</tr></thead><tbody><tr>"
        "<td>Job</td><td>Co</td><td>adzuna</td><td>100</td>"
        "<td>backend</td><td>senior</td><td></td>"
        "<td>https://example.com/very/long/path</td>"
        "</tr></tbody></table>"
    )
    result = _prepare_html_for_pdf(html)
    assert 'class="wide-table"' in result


def test_pdf_render_mocked_weasyprint(tmp_path: Path):
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1", source="remotive", title="Backend", company="Co",
        url="https://x.com", description="Python AWS",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    md_path = tmp_path / "market_fit_report.md"
    pdf_path = tmp_path / "market_fit_report.pdf"
    write_report_markdown(context, "Summary", md_path)

    mock_html_cls = MagicMock()
    mock_html_cls.return_value.write_pdf = MagicMock()

    with patch(
        "src.analysis.pdf_renderer._import_weasyprint_html",
        return_value=mock_html_cls,
    ):
        result, warning = render_pdf_from_markdown(md_path, pdf_path)

    assert warning is None
    assert result == pdf_path
    called_html = mock_html_cls.call_args.kwargs["string"]
    assert "Career Market Fit Report" in called_html
    assert "<table>" in called_html or 'class="wide-table"' in called_html
    mock_html_cls.return_value.write_pdf.assert_called_once_with(str(pdf_path))


def test_pdf_multiple_jobs_via_mock(tmp_path: Path):
    jobs = [
        TopJobSummary(
            title=f"Engineer {i}",
            company="Co",
            source="remotive",
            fit_score=80.0,
            primary_track="backend_cloud",
            matched_skills=["Python"],
            missing_skills=["Kubernetes"],
            seniority_estimate="senior",
            url=f"https://remotive.com/remote-jobs/software-dev/{i}-long-slug-path",
        )
        for i in range(5)
    ]
    context = ReportSummaryContext(
        resume_skills=["Python"],
        total_jobs_analyzed=5,
        jobs_by_source={"remotive": 5},
        jobs_by_track={"backend_cloud": 5},
        avg_fit_by_track={"backend_cloud": 80.0},
        top_requested_skills=[],
        top_missing_skills=[],
        top_matching_jobs=jobs,
        per_source_summary=[],
        study_recommendation="Study Kubernetes.",
    )
    md_path = tmp_path / "market_fit_report.md"
    pdf_path = tmp_path / "market_fit_report.pdf"
    write_report_markdown(context, "Executive summary paragraph.", md_path)

    result, warning = mock_pdf_render(md_path, pdf_path)
    assert warning is None
    assert result == pdf_path
    assert pdf_path.exists()


def test_pdf_graceful_skip_on_import_error(tmp_path: Path):
    md_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    md_path.write_text("# Title\n\nBody", encoding="utf-8")

    with patch(
        "src.analysis.pdf_renderer._import_weasyprint_html",
        side_effect=ImportError("no weasyprint"),
    ):
        result, warning = render_pdf_from_markdown(md_path, pdf_path)

    assert result is None
    assert warning == PDF_UNAVAILABLE_MSG


def test_pdf_graceful_skip_on_missing_system_libs(tmp_path: Path):
    md_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    md_path.write_text("# Title\n\nBody", encoding="utf-8")

    with patch(
        "src.analysis.pdf_renderer._import_weasyprint_html",
        side_effect=OSError("cannot load library 'libgobject-2.0-0'"),
    ):
        result, warning = render_pdf_from_markdown(md_path, pdf_path)

    assert result is None
    assert warning == PDF_UNAVAILABLE_MSG


def test_pdf_graceful_skip_on_render_error(tmp_path: Path):
    md_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    md_path.write_text("# Title\n\n| A | B |\n| --- | --- |\n| 1 | 2 |", encoding="utf-8")

    mock_html_cls = MagicMock()
    mock_html_cls.return_value.write_pdf.side_effect = RuntimeError("render failed")

    with patch(
        "src.analysis.pdf_renderer._import_weasyprint_html",
        return_value=mock_html_cls,
    ):
        result, warning = render_pdf_from_markdown(md_path, pdf_path)

    assert result is None
    assert warning is not None
    assert "PDF generation unavailable" in warning
