from src.analysis.matcher import match_job
from src.analysis.report_context import build_report_context
from src.models import JobPosting
from src.resume.skill_extractor import extract_skills


def test_report_context_excludes_descriptions():
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1", source="remotive", title="Eng", company="Co", url="https://x.com",
        description="SECRET DESCRIPTION TEXT",
    )
    match = match_job(job, resume)
    context = build_report_context(resume, [match])
    payload = context.model_dump_json()
    assert "SECRET DESCRIPTION TEXT" not in payload
    assert context.top_matching_jobs[0].title == "Eng"


def test_top_20_filter():
    resume = extract_skills("Python")
    jobs = [
        JobPosting(
            id=str(i), source="t", title=f"Job {i}", company="C",
            url=f"https://x.com/{i}", description="Python AWS",
        )
        for i in range(25)
    ]
    matches = [match_job(j, resume) for j in jobs]
    context = build_report_context(resume, matches)
    assert len(context.top_matching_jobs) <= 20
