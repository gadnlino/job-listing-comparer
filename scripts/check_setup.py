#!/usr/bin/env python3
"""Print setup health for local development."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ok(message: str) -> None:
    print(f"✓ {message}")


def warn(message: str) -> None:
    print(f"⚠ {message}")


def fail(message: str) -> None:
    print(f"✗ {message}")


def check_python() -> bool:
    version = sys.version_info
    if version >= (3, 11):
        ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    fail(f"Python 3.11+ required (found {version.major}.{version.minor})")
    return False


def check_imports() -> bool:
    required = ["fastapi", "httpx", "markdown", "pypdf"]
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        fail(f"Missing packages: {', '.join(missing)} (run: make setup)")
        return False
    ok("Python dependencies importable")
    return True


def check_weasyprint() -> bool:
    try:
        from src.analysis.pdf_renderer import _import_weasyprint_html

        _import_weasyprint_html()
        ok("WeasyPrint ready (PDF generation enabled)")
        return True
    except Exception as exc:
        warn(f"WeasyPrint unavailable — PDFs will be skipped ({exc})")
        if sys.platform == "darwin":
            warn("On macOS run: make setup-pdf")
        return False


def check_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        ok(".env present")
    else:
        warn(".env missing (run: make setup)")

    adzuna_id = os.getenv("ADZUNA_APP_ID", "").strip()
    adzuna_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    if adzuna_id and adzuna_key:
        ok("Adzuna credentials configured")
    else:
        warn("Adzuna not configured — Remotive + Arbeitnow only")


def check_ollama() -> None:
    import httpx

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        if response.status_code == 200:
            ok(f"Ollama reachable at {base_url}")
            return
    except Exception:
        pass
    warn("Ollama not reachable — template executive summary will be used")


def check_dirs() -> None:
    for relative in ("data/uploads", "data/raw", "data/processed", "reports"):
        path = ROOT / relative
        if path.is_dir():
            ok(f"{relative}/ exists")
        else:
            warn(f"{relative}/ missing (run: make setup)")


def main() -> int:
    print("Career Market Fit Scanner — setup check\n")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    checks = [
        check_python(),
        check_imports(),
    ]
    check_dirs()
    check_env()
    check_weasyprint()
    check_ollama()
    print("\nRun the app with: make run")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
