import json
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF
from pypdf import PdfWriter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def httpx_response(
    status_code: int = 200,
    json_data: dict | list | None = None,
    *,
    method: str = "GET",
    url: str = "https://example.com",
) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=json_data,
        request=httpx.Request(method, url),
    )


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        8,
        "Skills: Python, AWS, Docker, Kubernetes, Terraform, PostgreSQL, REST APIs\n"
        "Experience with serverless and microservices on AWS Lambda and DynamoDB.",
    )
    return bytes(pdf.output())


def mock_pdf_render(md_path, pdf_path):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 test")
    return pdf_path, None


@pytest.fixture
def blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def sample_resume_pdf(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    text_path = tmp_path / "resume_text.txt"
    text_path.write_text(
        "Skills: Python, AWS, Docker, Kubernetes, Terraform, PostgreSQL, REST APIs\n"
        "Experience with serverless and microservices on AWS Lambda and DynamoDB.",
        encoding="utf-8",
    )
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    return pdf_path


@pytest.fixture
def remotive_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "remotive_response.json").read_text())


@pytest.fixture
def adzuna_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "adzuna_response.json").read_text())


@pytest.fixture
def arbeitnow_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "arbeitnow_response.json").read_text())


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    import src.config as config

    uploads = tmp_path / "uploads"
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    raw = tmp_path / "raw"

    monkeypatch.setattr(config, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(config, "PROCESSED_DIR", processed)
    monkeypatch.setattr(config, "REPORTS_DIR", reports)
    monkeypatch.setattr(config, "RAW_DIR", raw)

    import src.analysis.pipeline as pipeline_module
    import src.app as app_module

    monkeypatch.setattr(pipeline_module, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(pipeline_module, "PROCESSED_DIR", processed)
    monkeypatch.setattr(pipeline_module, "REPORTS_DIR", reports)

    monkeypatch.setattr(app_module, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(app_module, "PROCESSED_DIR", processed)
    monkeypatch.setattr(app_module, "REPORTS_DIR", reports)

    uploads.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    def mock_validate_job_links(matches):
        return [
            m.model_copy(update={"link_status": "accessible", "link_status_code": 200})
            for m in matches
        ]

    monkeypatch.setattr("src.analysis.link_validator.validate_job_links", mock_validate_job_links)

    return TestClient(app_module.app)
