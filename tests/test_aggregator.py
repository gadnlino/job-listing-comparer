from src.analysis.aggregator import top_missing_skills, top_requested_skills
from src.analysis.matcher import match_job
from src.models import JobPosting
from src.resume.skill_extractor import extract_skills


def test_top_skills_ranking():
    resume = extract_skills("Python AWS")
    jobs = [
        JobPosting(
            id="1", source="t", title="Eng", company="C", url="u",
            description="Python AWS Kubernetes Terraform",
        ),
        JobPosting(
            id="2", source="t", title="Eng", company="C", url="u2",
            description="Python AWS Kubernetes Docker",
        ),
    ]
    matches = [match_job(j, resume) for j in jobs]
    missing = top_missing_skills(matches)
    requested = top_requested_skills(matches)
    assert missing
    assert requested
    assert missing[0].count >= 1
