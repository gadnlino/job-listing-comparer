from unittest.mock import patch

import httpx

from tests.conftest import httpx_response, mock_pdf_render


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Career Market Fit Scanner" in response.text
    assert "Analyze" in response.text
    assert 'id="analysis-progress"' in response.text
    assert 'id="loading-status"' in response.text
    assert "/analyze/stream" in response.text
    assert "getReader" in response.text


def test_home_page_loading_overlay_accessibility(client):
    response = client.get("/")
    assert 'aria-live="polite"' in response.text
    assert 'aria-busy' in response.text


def test_analyze_rejects_non_pdf(client):
    response = client.post(
        "/analyze",
        files={"file": ("doc.txt", b"hello", "text/plain")},
        data={"max_results": "10", "source": "all", "adzuna_country": "all"},
    )
    assert response.status_code == 400


def test_download_404(client):
    response = client.get("/download/market_fit_report.pdf")
    assert response.status_code == 404


def test_report_print_route_returns_html(client, monkeypatch):
    import src.app as app_module

    monkeypatch.setattr("src.config.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.app.PDF_RENDERER", "browser")

    md_path = app_module.REPORTS_DIR / "market_fit_report.md"
    md_path.write_text("# Career Market Fit Report\n\n## Executive Summary\n\nHello", encoding="utf-8")

    response = client.get("/report/print")
    assert response.status_code == 200
    assert "html2pdf" in response.text
    assert "market_fit_report.pdf" in response.text
    assert "Executive Summary" in response.text


def test_report_print_route_404_when_missing(client):
    response = client.get("/report/print")
    assert response.status_code == 404


def test_analyze_auto_opens_print_route_in_browser_mode(
    client, sample_pdf_bytes, remotive_fixture, monkeypatch
):
    monkeypatch.setattr("src.config.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.app.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.analysis.pipeline.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.analysis.report_generator.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.analysis.pdf_renderer.PDF_RENDERER", "browser")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", True)):
            response = client.post(
                "/analyze",
                files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
            )

    assert response.status_code == 200
    assert "var url = '/report/print'" in response.text
    assert "var url = '/download/market_fit_report.pdf'" not in response.text


def test_analyze_with_mocked_collectors(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
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
                    "/analyze",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
                )

    assert response.status_code == 200
    assert "Analysis Results" in response.text
    assert "var url = '/download/market_fit_report.pdf'" in response.text
    assert "pdf-blocked-notice" in response.text


def test_pdf_inline_headers(client):
    import src.app as app_module

    pdf_path = app_module.REPORTS_DIR / "market_fit_report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    response = client.get("/download/market_fit_report.pdf")
    assert response.status_code == 200
    assert "inline" in response.headers.get("content-disposition", "")


def test_no_auto_open_when_no_jobs(client, sample_pdf_bytes, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    with patch("src.collectors.orchestrator.JobOrchestrator.collect") as mock_collect:
        from src.collectors.orchestrator import CollectionResult

        mock_collect.return_value = CollectionResult(jobs=[], warnings=[], sources_used=[])
        response = client.post(
            "/analyze",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            data={"max_results": "10", "source": "all", "adzuna_country": "all"},
        )
    assert "window.open" not in response.text


def test_inaccessible_jobs_excluded_from_results(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    def mock_validate(matches, reporter=None):
        updated = []
        for i, m in enumerate(matches):
            status = "inaccessible" if i == 0 else "accessible"
            updated.append(m.model_copy(update={"link_status": status, "link_status_code": 404 if i == 0 else 200}))
        return updated

    monkeypatch.setattr("src.analysis.link_validator.validate_job_links", mock_validate)
    monkeypatch.setattr("src.analysis.pipeline.validate_job_links", mock_validate)

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Summary", False)):
            with patch("src.analysis.report_generator.render_pdf_from_markdown", side_effect=mock_pdf_render):
                response = client.post(
                    "/analyze",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "10", "source": "remotive", "adzuna_country": "all"},
                )

    assert response.status_code == 200
    assert "Unavailable" not in response.text
