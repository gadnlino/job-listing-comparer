from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT_DIR / "reports"
SKILLS_PATH = Path(__file__).resolve().parent / "resume" / "skills.json"
TEMPLATES_DIR = Path(__file__).resolve().parent / "web" / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "web" / "static"

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# LLM configuration (preferred). Backwards-compatible with Ollama env vars.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", OLLAMA_BASE_URL).rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", OLLAMA_MODEL).strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()

_pdf_renderer = os.getenv("PDF_RENDERER", "weasyprint").strip().lower()
if _pdf_renderer not in {"browser", "weasyprint", "off"}:
    _pdf_renderer = "weasyprint"
PDF_RENDERER = _pdf_renderer

LINK_VALIDATION_ENABLED = os.getenv("LINK_VALIDATION_ENABLED", "true").lower() in ("1", "true", "yes")
LINK_VALIDATION_MAX_JOBS = int(os.getenv("LINK_VALIDATION_MAX_JOBS", "200"))
LINK_VALIDATION_TIMEOUT_SECONDS = float(os.getenv("LINK_VALIDATION_TIMEOUT_SECONDS", "10"))
LINK_VALIDATION_MIN_BODY_BYTES = int(os.getenv("LINK_VALIDATION_MIN_BODY_BYTES", "500"))

DEFAULT_QUERIES = [
    "backend engineer aws",
    "python aws engineer",
    "serverless engineer",
    "api integration engineer",
    "platform engineer",
    "site reliability engineer",
    "cloud security engineer",
    "aws security engineer",
    "devsecops engineer",
    "llm engineer",
    "ai engineer rag",
    "genai engineer",
    "data engineer aws",
]

DEFAULT_ADZUNA_COUNTRIES = ["gb", "us", "es", "de", "nl", "ie"]

WEIGHT_VALUES = {"high": 3.0, "medium": 2.0, "low": 1.0}

TRACK_KEYWORDS = {
    "backend_cloud": [
        "backend", "api", "python", "node", "typescript", "aws", "lambda",
        "serverless", "microservices", "postgres", "dynamodb", "sqs", "sns",
    ],
    "ai_engineering": [
        "ai engineer", "llm", "rag", "genai", "generative ai", "agents",
        "vector database", "embeddings", "langchain", "llamaindex", "openai",
        "anthropic", "evaluation", "prompt engineering",
    ],
    "cloud_security": [
        "cloud security", "aws security", "iam", "security", "devsecops",
        "compliance", "soc2", "iso 27001", "threat modeling", "vulnerability",
        "secrets management", "zero trust",
    ],
    "platform_engineering": [
        "platform engineer", "sre", "kubernetes", "terraform", "ci/cd",
        "observability", "grafana", "prometheus", "datadog", "infrastructure",
        "developer platform", "reliability",
    ],
    "data_engineering": [
        "data engineer", "pipelines", "etl", "elt", "kafka", "airflow", "dbt",
        "spark", "data warehouse", "snowflake", "bigquery", "lakehouse",
    ],
}

TRACK_PRIORITY = [
    "backend_cloud",
    "platform_engineering",
    "ai_engineering",
    "cloud_security",
    "data_engineering",
]

SENIORITY_KEYWORDS = [
    ("manager", ["engineering manager", "manager"]),
    ("principal", ["principal"]),
    ("staff", ["staff"]),
    ("lead", ["lead", "team lead"]),
    ("senior", ["senior", "sr."]),
    ("mid", ["mid", "software engineer ii", "engineer ii"]),
    ("junior", ["junior", "entry level", "graduate"]),
]
