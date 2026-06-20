from unittest.mock import patch

import httpx

from src.collectors.orchestrator import JobOrchestrator, deduplicate_jobs
from src.models import JobPosting
from tests.conftest import httpx_response


def test_deduplicate_by_url():
    jobs = [
        JobPosting(id="1", source="remotive", title="A", company="C", url="https://x.com/1", description=""),
        JobPosting(id="2", source="adzuna", title="A", company="C", url="https://x.com/1", description=""),
    ]
    assert len(deduplicate_jobs(jobs)) == 1


def test_orchestrator_zero_config(remotive_fixture, arbeitnow_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, arbeitnow_fixture, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        result = JobOrchestrator().collect(["remotive", "adzuna", "arbeitnow"], max_results=50)

    assert any("Adzuna skipped" in w for w in result.warnings)
    assert "remotive" in result.sources_used or "arbeitnow" in result.sources_used


def test_orchestrator_isolates_source_failure(remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        raise httpx.ConnectError("fail")

    with patch("httpx.get", side_effect=mock_get):
        result = JobOrchestrator().collect(["remotive", "arbeitnow"], max_results=20)

    assert result.jobs
