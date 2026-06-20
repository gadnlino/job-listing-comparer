import json
from unittest.mock import patch

import httpx
import pytest

from src.analysis.progress import (
    ProgressReporter,
    done_event,
    error_event,
    format_ndjson_line,
    progress_event,
)
from tests.conftest import httpx_response, mock_pdf_render


def test_progress_event_helpers():
    event = progress_event(
        "Validating link 2/5: Engineer",
        stage="validate",
        source="remotive",
        current=2,
        total=5,
        title="Engineer",
    )
    assert event["type"] == "progress"
    assert event["stage"] == "validate"
    assert event["current"] == 2
    line = format_ndjson_line(event)
    assert json.loads(line) == event

    assert error_event("bad")["type"] == "error"
    assert done_event("/analyze/result")["redirect"] == "/analyze/result"


def test_progress_reporter_sink():
    events = []
    reporter = ProgressReporter(_sink=events.append)
    reporter.emit("hello", stage="parse")
    assert len(events) == 1
    assert events[0]["message"] == "hello"


def test_analyze_stream_progress_and_done(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", False)):
            with patch("src.analysis.report_generator.render_pdf_from_markdown", side_effect=mock_pdf_render):
                response = client.post(
                    "/analyze/stream",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
                )

    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers.get("content-type", "")

    events = [json.loads(line) for line in response.text.strip().split("\n") if line.strip()]
    types = [e["type"] for e in events]
    assert "progress" in types
    assert events[-1]["type"] == "done"
    assert events[-1]["redirect"] == "/analyze/result"

    stages = {e.get("stage") for e in events if e["type"] == "progress"}
    assert "parse" in stages
    assert "collect" in stages
    assert "match" in stages


def test_analyze_stream_validate_stage_fields(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", False)):
            with patch("src.analysis.report_generator.render_pdf_from_markdown", side_effect=mock_pdf_render):
                response = client.post(
                    "/analyze/stream",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
                )

    validate_events = [
        json.loads(line)
        for line in response.text.strip().split("\n")
        if line.strip() and json.loads(line).get("stage") == "validate"
    ]
    assert validate_events
    sample = validate_events[0]
    assert sample["type"] == "progress"
    assert "message" in sample
    assert "total" in sample


def test_analyze_stream_error_on_bad_input(client):
    response = client.post(
        "/analyze/stream",
        files={"file": ("doc.txt", b"hello", "text/plain")},
        data={"max_results": "10", "source": "all", "adzuna_country": "all"},
    )
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().split("\n") if line.strip()]
    assert events[-1]["type"] == "error"
    assert "PDF" in events[-1]["message"]


def test_analyze_result_after_stream(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", False)):
            with patch("src.analysis.report_generator.render_pdf_from_markdown", side_effect=mock_pdf_render):
                stream_response = client.post(
                    "/analyze/stream",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
                )

    assert json.loads(stream_response.text.strip().split("\n")[-1])["type"] == "done"

    result_response = client.get("/analyze/result")
    assert result_response.status_code == 200
    assert "Analysis Results" in result_response.text


def test_analyze_result_redirects_without_session(client):
    import src.app as app_module

    app_module._last_analysis_view = None
    response = client.get("/analyze/result", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
