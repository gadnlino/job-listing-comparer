from pathlib import Path

from src.analysis.matcher import match_job
from src.analysis.report_generator import write_job_matches_csv
from src.models import JobPosting
from src.resume.skill_extractor import extract_skills


def test_csv_columns_and_sort(tmp_path: Path):
    resume = extract_skills("Python AWS")
    jobs = [
        JobPosting(id="1", source="a", title="Low", company="C", url="u1", description="Python"),
        JobPosting(id="2", source="a", title="High", company="C", url="u2", description="Python AWS Docker Kubernetes Terraform"),
    ]
    matches = [match_job(j, resume) for j in jobs]
    matches[0] = matches[0].model_copy(update={"link_status": "accessible", "link_status_code": 200})
    matches[1] = matches[1].model_copy(update={"link_status": "unknown", "link_status_code": 403})
    path = tmp_path / "job_matches.csv"
    write_job_matches_csv(matches, path)
    content = path.read_text(encoding="utf-8")
    header = content.splitlines()[0]
    assert "fit_score" in header
    assert "link_status" in header
    assert "link_status_code" in header
    lines = content.strip().splitlines()
    assert len(lines) == 3
    scores = [float(line.split(",")[8]) for line in lines[1:]]
    assert scores == sorted(scores, reverse=True)
    assert "accessible" in content
    assert "unknown" in content
