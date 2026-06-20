from unittest.mock import patch

import httpx

from src.models import DetectedSkill, JobMatch, JobPosting


def test_models_validation():
    skill = DetectedSkill(canonical_name="Python", confidence=0.9, weight="medium")
    job = JobPosting(id="1", source="t", title="T", company="C", url="u", description="d")
    match = JobMatch(
        job=job,
        primary_track="backend_cloud",
        track_scores={"backend_cloud": 2},
        fit_score=50.0,
        matched_skills=["Python"],
        missing_skills=["Kubernetes"],
        seniority_estimate="senior",
    )
    assert skill.canonical_name == "Python"
    assert match.fit_score == 50.0
