from pathlib import Path
from unittest.mock import patch

import pytest

from src.analysis.matcher import match_job
from src.analysis.report_context import build_report_context
from src.analysis.report_generator import generate_reports
from src.models import JobPosting
from src.resume.skill_extractor import extract_skills


def test_browser_mode_skips_server_pdf(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("src.analysis.report_generator.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.analysis.pdf_renderer.PDF_RENDERER", "browser")

    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1",
        source="remotive",
        title="Backend",
        company="Co",
        url="https://example.com",
        description="Python AWS",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)

    with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", True)):
        with patch("src.analysis.report_generator.render_pdf_from_markdown") as mock_render:
            _, md_path, pdf_path, _, _, warning = generate_reports(matches, context, tmp_path)

    mock_render.assert_not_called()
    assert md_path.exists()
    assert pdf_path is None
    assert warning is None


def test_weasyprint_mode_calls_server_pdf(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("src.analysis.report_generator.PDF_RENDERER", "weasyprint")
    monkeypatch.setattr("src.analysis.pdf_renderer.PDF_RENDERER", "weasyprint")

    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1",
        source="remotive",
        title="Backend",
        company="Co",
        url="https://example.com",
        description="Python AWS",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    pdf_path = tmp_path / "market_fit_report.pdf"

    with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", True)):
        with patch(
            "src.analysis.report_generator.render_pdf_from_markdown",
            return_value=(pdf_path, None),
        ) as mock_render:
            _, _, result_pdf, _, _, _ = generate_reports(matches, context, tmp_path)

    mock_render.assert_called_once()
    assert result_pdf == pdf_path
