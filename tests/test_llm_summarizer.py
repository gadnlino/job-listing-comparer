from unittest.mock import patch

import httpx

from src.analysis.report_generator import generate_llm_summary, generate_template_summary
from src.models import ReportSummaryContext, SkillFrequency, TopJobSummary
from tests.conftest import httpx_response


def _sample_context() -> ReportSummaryContext:
    return ReportSummaryContext(
        resume_skills=["Python", "AWS"],
        total_jobs_analyzed=1,
        jobs_by_source={"remotive": 1},
        jobs_by_track={"backend_cloud": 1},
        avg_fit_by_track={"backend_cloud": 75.0},
        top_requested_skills=[SkillFrequency(skill="Python", count=1)],
        top_missing_skills=[SkillFrequency(skill="Kubernetes", count=1)],
        top_matching_jobs=[
            TopJobSummary(
                title="Eng", company="Co", source="remotive", fit_score=75.0,
                primary_track="backend_cloud", matched_skills=["Python"],
                missing_skills=["Kubernetes"], seniority_estimate="senior",
                url="https://example.com",
            )
        ],
        per_source_summary=[],
        study_recommendation="Focus on Kubernetes.",
    )


def test_template_fallback():
    context = _sample_context()
    summary = generate_template_summary(context)
    assert "Python" in summary
    assert "1" in summary


def test_llm_prompt_structured_only():
    context = _sample_context()
    with patch("httpx.post") as mock_post:
        mock_post.return_value = httpx_response(
            200,
            {"response": "Summary from LLM."},
            method="POST",
            url="http://localhost:11434/api/generate",
        )
        summary, used = generate_llm_summary(context)
    assert used is True
    assert "Summary" in summary
    call_args = mock_post.call_args
    prompt = call_args.kwargs["json"]["prompt"]
    assert "Python" in prompt
    assert "SECRET" not in prompt


def test_llm_fallback_on_failure():
    context = _sample_context()
    with patch("httpx.post", side_effect=httpx.ConnectError("down")):
        summary, used = generate_llm_summary(context)
    assert used is False
    assert summary
