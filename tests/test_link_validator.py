from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.analysis.link_validator import (
    _classify_response,
    _validate_single_url,
    build_link_validation_warnings,
    filter_displayable_matches,
    link_validation_summary,
    validate_job_links,
)
from src.analysis.matcher import match_job
from src.models import JobMatch, JobPosting
from src.resume.skill_extractor import extract_skills


def _make_match(url: str, source: str = "remotive") -> JobMatch:
    resume = extract_skills("Python AWS")
    job = JobPosting(
        id="1",
        source=source,
        title="Engineer",
        company="Co",
        url=url,
        description="Python AWS Docker",
    )
    return match_job(job, resume)


def test_classify_response_accessible():
    assert _classify_response(200, 600, 500) == "accessible"


def test_classify_response_small_body_inaccessible():
    assert _classify_response(200, 100, 500) == "inaccessible"


def test_classify_response_403_unknown():
    assert _classify_response(403, 600, 500) == "unknown"


def test_classify_response_429_unknown():
    assert _classify_response(429, 600, 500) == "unknown"


def test_classify_response_404_inaccessible():
    assert _classify_response(404, 0, 500) == "inaccessible"


def test_empty_url_inaccessible():
    status, code = _validate_single_url("  ", 10.0, 500)
    assert status == "inaccessible"
    assert code is None


def test_validate_single_url_accessible():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_bytes.return_value = [b"x" * 600]

    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_response)
    mock_stream.__exit__ = MagicMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("src.analysis.link_validator.httpx.Client", return_value=mock_client):
        status, code = _validate_single_url("https://example.com/job", 10.0, 500)

    assert status == "accessible"
    assert code == 200
    mock_client.stream.assert_called_once_with("GET", "https://example.com/job")


def test_validate_single_url_timeout():
    mock_client = MagicMock()
    mock_client.stream.side_effect = httpx.TimeoutException("timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("src.analysis.link_validator.httpx.Client", return_value=mock_client):
        status, code = _validate_single_url("https://example.com/job", 10.0, 500)

    assert status == "inaccessible"
    assert code is None


def test_validate_job_links_batch(monkeypatch):
    monkeypatch.setattr("src.analysis.link_validator.LINK_VALIDATION_ENABLED", True)

    def mock_validate(url, timeout, min_body):
        if "bad" in url:
            return "inaccessible", 404
        if "blocked" in url:
            return "unknown", 403
        return "accessible", 200

    matches = [
        _make_match("https://example.com/good"),
        _make_match("https://example.com/bad"),
        _make_match("https://example.com/blocked"),
    ]

    with patch("src.analysis.link_validator._validate_single_url", side_effect=mock_validate):
        result = validate_job_links(matches)

    assert result[0].link_status == "accessible"
    assert result[1].link_status == "inaccessible"
    assert result[2].link_status == "unknown"


def test_validate_job_links_disabled(monkeypatch):
    monkeypatch.setattr("src.analysis.link_validator.LINK_VALIDATION_ENABLED", False)
    matches = [_make_match("https://example.com/job")]
    result = validate_job_links(matches)
    assert result[0].link_status == "unknown"
    assert result[0].link_status_code is None


def test_filter_displayable_matches(monkeypatch):
    monkeypatch.setattr("src.analysis.link_validator.LINK_VALIDATION_ENABLED", True)
    matches = [
        _make_match("https://example.com/a").model_copy(update={"link_status": "accessible"}),
        _make_match("https://example.com/b").model_copy(update={"link_status": "inaccessible"}),
        _make_match("https://example.com/c").model_copy(update={"link_status": "unknown"}),
    ]
    filtered = filter_displayable_matches(matches)
    assert len(filtered) == 2
    assert all(m.link_status in ("accessible", "unknown") for m in filtered)


def test_filter_displayable_when_disabled(monkeypatch):
    monkeypatch.setattr("src.analysis.link_validator.LINK_VALIDATION_ENABLED", False)
    matches = [
        _make_match("https://example.com/a").model_copy(update={"link_status": "inaccessible"}),
    ]
    assert len(filter_displayable_matches(matches)) == 1


def test_link_validation_summary():
    matches = [
        _make_match("https://a.com", "adzuna").model_copy(update={"link_status": "accessible"}),
        _make_match("https://b.com", "adzuna").model_copy(update={"link_status": "inaccessible"}),
        _make_match("https://c.com", "remotive").model_copy(update={"link_status": "unknown"}),
    ]
    summary = link_validation_summary(matches)
    assert summary["adzuna"]["accessible"] == 1
    assert summary["adzuna"]["inaccessible"] == 1
    assert summary["adzuna"]["excluded"] == 1
    assert summary["remotive"]["unknown"] == 1


def test_build_link_validation_warnings():
    summary = {
        "adzuna": {
            "accessible": 2,
            "inaccessible": 8,
            "unknown": 0,
            "excluded": 8,
            "validated": 10,
        }
    }
    warnings = build_link_validation_warnings(summary)
    assert len(warnings) == 1
    assert "adzuna" in warnings[0].lower()
    assert "excluded" in warnings[0].lower() or "8" in warnings[0]
