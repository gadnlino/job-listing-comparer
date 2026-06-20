.PHONY: help setup install install-system-deps check run test clean setup-pdf

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PY := $(BIN)/python
UVICORN := $(BIN)/uvicorn

DATA_DIRS := data/uploads data/raw data/processed reports

help:
	@echo "Career Market Fit Scanner"
	@echo ""
	@echo "  make setup      Full setup: system libs, venv, deps, dirs, .env, verify"
	@echo "  make check      Verify dependencies and optional services"
	@echo "  make run        Start the web app (http://127.0.0.1:8000)"
	@echo "  make test       Run pytest"
	@echo "  make clean      Remove virtualenv"

setup: install-system-deps install verify
	@echo ""
	@echo "Setup complete. Start the app with:"
	@echo "  make run"

install: $(VENV)/bin/activate dirs env
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

dirs:
	@mkdir -p $(DATA_DIRS)

env:
	@if [ ! -f .env ]; then cp .env.example .env && echo "✓ Created .env from .env.example"; fi

install-system-deps:
	@bash scripts/install_system_deps.sh || true

verify: $(VENV)/bin/activate
	@$(PY) scripts/check_setup.py

# Backward-compatible alias
setup-pdf: install-system-deps

check: verify

run: $(VENV)/bin/activate
	$(UVICORN) src.app:app --reload

test: $(VENV)/bin/activate
	$(PY) -m pytest

clean:
	rm -rf $(VENV)
