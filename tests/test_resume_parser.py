from pathlib import Path

import pytest

from src.resume.parser import (
    EmptyResumeTextError,
    ResumeParseError,
    extract_text_from_pdf,
    save_resume_text,
)


def test_extract_text_from_valid_pdf(tmp_path: Path, sample_pdf_bytes: bytes):
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    text = extract_text_from_pdf(pdf_path)
    assert "Python" in text
    assert "AWS" in text


def test_invalid_pdf_raises(tmp_path: Path):
    bad_path = tmp_path / "bad.pdf"
    bad_path.write_bytes(b"not a pdf")
    with pytest.raises(ResumeParseError):
        extract_text_from_pdf(bad_path)


def test_empty_pdf_raises(tmp_path: Path, blank_pdf_bytes: bytes):
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(blank_pdf_bytes)
    with pytest.raises(EmptyResumeTextError):
        extract_text_from_pdf(pdf_path)


def test_save_resume_text(tmp_path: Path):
    out = tmp_path / "processed" / "resume_text.txt"
    save_resume_text("hello world", out)
    assert out.read_text(encoding="utf-8") == "hello world"
