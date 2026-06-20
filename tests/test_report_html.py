from pathlib import Path

from src.analysis.matcher import match_job
from src.analysis.pdf_renderer import build_report_content, build_report_html
from src.analysis.report_context import build_report_context
from src.analysis.report_generator import write_report_markdown
from src.models import JobPosting
from src.resume.skill_extractor import extract_skills


def test_build_report_html_includes_required_sections(tmp_path: Path):
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1",
        source="remotive",
        title="Backend Engineer",
        company="Co",
        url="https://example.com/job",
        description="Python AWS Kubernetes",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    md_path = tmp_path / "market_fit_report.md"
    write_report_markdown(context, "Executive summary paragraph.", md_path)

    html_body, styles = build_report_content(md_path)
    html_full = build_report_html(md_path)

    assert "Career Market Fit Report" in html_body
    assert "Executive Summary" in html_body
    assert "Market Overview" in html_body
    assert "<table>" in html_body
    assert "font-family" in styles
    assert "Career Market Fit Report" in html_full
    assert "<html" in html_full
