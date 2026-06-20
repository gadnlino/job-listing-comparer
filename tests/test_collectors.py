from unittest.mock import patch

from src.collectors.adzuna import AdzunaCollector
from src.collectors.arbeitnow import ArbeitnowCollector
from src.collectors.remotive import RemotiveCollector
from tests.conftest import httpx_response


def test_remotive_normalization(remotive_fixture):
    collector = RemotiveCollector()
    job = collector._normalize(remotive_fixture["jobs"][0])
    assert job.source == "remotive"
    assert job.title == "Senior Python AWS Engineer"
    assert job.company == "Acme Corp"


def test_remotive_single_batch_call(remotive_fixture):
    collector = RemotiveCollector()
    with patch("httpx.get") as mock_get:
        mock_get.return_value = httpx_response(200, remotive_fixture, url="https://remotive.com/api/remote-jobs")
        collector.fetch_batch()
        collector.search_jobs("python aws", 10)
        assert mock_get.call_count == 1


def test_adzuna_normalization(adzuna_fixture):
    collector = AdzunaCollector()
    job = collector._normalize(adzuna_fixture["results"][0], "gb")
    assert job.source == "adzuna"
    assert job.country == "gb"
    assert job.title == "Backend Engineer AWS"


def test_adzuna_skipped_without_credentials(monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")
    collector = AdzunaCollector()
    assert collector.search_jobs("python", 10) == []


def test_arbeitnow_normalization(arbeitnow_fixture):
    collector = ArbeitnowCollector()
    job = collector._normalize(arbeitnow_fixture["data"][0])
    assert job.source == "arbeitnow"
    assert job.remote_type == "remote"
