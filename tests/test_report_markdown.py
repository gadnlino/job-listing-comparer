from datetime import datetime
from pathlib import Path

from src.analysis.matcher import match_job
from src.analysis.report_context import build_report_context
from src.analysis.report_generator import build_report_markdown, write_report_markdown
from src.models import JobPosting, ReportSummaryContext, TopJobSummary
from src.resume.skill_extractor import extract_skills


def test_markdown_all_sections():
    resume = extract_skills("Python AWS Kubernetes")
    job = JobPosting(
        id="1", source="remotive", title="Backend Engineer", company="Co",
        url="https://x.com", description="SECRET DESCRIPTION",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    content = build_report_markdown(context, "Executive summary text.", datetime(2026, 6, 19, 12, 0))

    assert "# Career Market Fit Report" in content
    assert "Generated: 2026-06-19" in content
    assert "## Executive Summary" in content
    assert "## Resume Skills Detected" in content
    assert "## Market Overview" in content
    assert "### Jobs by Source" in content
    assert "### Jobs by Career Track" in content
    assert "## Top 20 Most Requested Skills" in content
    assert "## Top 20 Missing Skills" in content
    assert "## Per-Source Snapshot" in content
    assert "## Top 20 Matching Jobs" in content
    assert "## Study Recommendation" in content
    assert "Remotive" in content
    assert "SECRET DESCRIPTION" not in content


def test_markdown_gfm_tables():
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1", source="remotive", title="Backend", company="Co",
        url="https://x.com", description="Python AWS",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    content = build_report_markdown(context, "Summary", datetime(2026, 1, 1))

    assert "| Source | Jobs |" in content
    assert "| Track | Jobs | Avg Fit |" in content
    assert "| Title | Company | Source | Fit | Track | Seniority | Link Status | URL |" in content
    assert "| Source | Jobs | Avg Fit | Top Track |" in content


def test_markdown_top_20_table_rows():
    jobs = [
        TopJobSummary(
            title=f"Job {i}",
            company="Co",
            source="remotive",
            fit_score=float(i),
            primary_track="backend_cloud",
            matched_skills=["Python"],
            missing_skills=["Kubernetes"],
            seniority_estimate="senior",
            url=f"https://example.com/{i}",
        )
        for i in range(25)
    ]
    context = ReportSummaryContext(
        resume_skills=["Python"],
        total_jobs_analyzed=25,
        jobs_by_source={"remotive": 25},
        jobs_by_track={"backend_cloud": 25},
        avg_fit_by_track={"backend_cloud": 50.0},
        top_requested_skills=[],
        top_missing_skills=[],
        top_matching_jobs=jobs,
        per_source_summary=[],
        study_recommendation="Study Kubernetes.",
    )
    content = build_report_markdown(context, "Summary", datetime(2026, 1, 1))
    table_lines = [line for line in content.splitlines() if line.startswith("| Job ")]
    assert len(table_lines) == 20


def test_markdown_link_exclusions_note():
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1", source="remotive", title="Backend", company="Co",
        url="https://x.com", description="Python AWS",
    )
    match = match_job(job, resume).model_copy(update={"link_status": "accessible"})
    context = build_report_context(
        resume,
        [match],
        link_exclusions_by_source={"adzuna": 5},
    )
    content = build_report_markdown(context, "Summary", datetime(2026, 1, 1))
    assert "## Link Validation" in content
    assert "adzuna" in content
    assert "5 link(s) excluded" in content


def test_write_report_markdown(tmp_path: Path):
    resume = extract_skills("Python")
    job = JobPosting(
        id="1", source="remotive", title="Eng", company="Co",
        url="https://x.com", description="Python",
    )
    matches = [match_job(job, resume)]
    context = build_report_context(resume, matches)
    path = tmp_path / "market_fit_report.md"
    write_report_markdown(context, "Executive summary.", path)
    assert path.exists()
    assert "Career Market Fit Report" in path.read_text(encoding="utf-8")
