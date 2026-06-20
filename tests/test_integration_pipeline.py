from unittest.mock import patch

import httpx

from tests.conftest import httpx_response, mock_pdf_render


def test_integration_pipeline(client, sample_pdf_bytes, remotive_fixture, monkeypatch):
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_ID", "")
    monkeypatch.setattr("src.collectors.adzuna.ADZUNA_APP_KEY", "")

    def mock_get(url, *args, **kwargs):
        if "remotive" in url:
            return httpx_response(200, remotive_fixture, url=str(url))
        return httpx_response(200, {"data": [], "links": {}}, url=str(url))

    with patch("httpx.get", side_effect=mock_get):
        with patch("src.analysis.report_generator.generate_llm_summary", return_value=("Exec summary", False)):
            with patch("src.analysis.report_generator.render_pdf_from_markdown", side_effect=mock_pdf_render):
                response = client.post(
                    "/analyze",
                    files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
                    data={"max_results": "20", "source": "remotive", "adzuna_country": "all"},
                )

    assert response.status_code == 200
    import src.app as app_module

    assert (app_module.REPORTS_DIR / "job_matches.csv").exists()
    assert (app_module.REPORTS_DIR / "market_fit_report.md").exists()
    assert (app_module.REPORTS_DIR / "market_fit_report.pdf").exists()
