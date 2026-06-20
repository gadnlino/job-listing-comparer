from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ResumeParseError(Exception):
    pass


class EmptyResumeTextError(ResumeParseError):
    pass


def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        reader = PdfReader(str(pdf_path))
    except PdfReadError as exc:
        raise ResumeParseError("Unable to read PDF file.") from exc
    except Exception as exc:
        raise ResumeParseError("Unable to read PDF file.") from exc

    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)

    combined = "\n".join(parts).strip()
    if not combined:
        raise EmptyResumeTextError("No readable text could be extracted from the PDF.")
    return combined


def save_resume_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
