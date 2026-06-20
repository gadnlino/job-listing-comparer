from src.analysis.matcher import estimate_seniority, match_job
from src.models import DetectedSkill, JobPosting
from src.resume.skill_extractor import extract_skills


def test_fit_score_bounded():
    resume = extract_skills("Python AWS Docker Kubernetes Terraform PostgreSQL")
    job = JobPosting(
        id="1",
        source="test",
        title="Python AWS Engineer",
        company="Co",
        url="https://example.com",
        description="Python, AWS, Lambda, Kubernetes, Terraform required",
    )
    match = match_job(job, resume)
    assert 0 <= match.fit_score <= 100


def test_seniority_from_title():
    assert estimate_seniority("Senior Backend Engineer") == "senior"
    assert estimate_seniority("Junior Developer") == "junior"


def test_shared_extractor_on_job():
    job = JobPosting(
        id="1",
        source="test",
        title="LLM Engineer",
        company="Co",
        url="https://example.com",
        description="RAG, vector database, LLM evaluation",
    )
    resume = [DetectedSkill(canonical_name="Python", confidence=1.0, weight="medium")]
    match = match_job(job, resume)
    assert "LLM" in match.missing_skills or "RAG" in match.missing_skills
