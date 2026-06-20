## ADDED Requirements

### Requirement: Cloud deployment without local LLM or server PDF

The system SHALL support deploying the FastAPI app alone (without docker-compose llama sidecar or WeasyPrint) on memory-constrained hosts such as Railway free tier (~512 MB), using Groq for executive summaries and browser PDF generation.

#### Scenario: Railway free-tier recommended profile documented

- **WHEN** the user deploys to a lightweight cloud host
- **THEN** documentation recommends `PDF_RENDERER=browser`, Groq LLM env vars (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`), app-only Docker deploy, and optional tuning (`LINK_VALIDATION_ENABLED=false`, lower `max_results`) to reduce RAM and runtime

#### Scenario: App-only deploy without llama sidecar

- **WHEN** Groq env vars are configured
- **THEN** the app generates executive summaries without a local llama.cpp or Ollama container

#### Scenario: No WeasyPrint required on cloud profile

- **WHEN** `PDF_RENDERER=browser`
- **THEN** the server does not require WeasyPrint system libraries or server-side PDF file generation for a successful analysis workflow

#### Scenario: Outbound HTTPS to Groq

- **WHEN** Groq is configured
- **THEN** the app sends executive summary requests to the configured OpenAI-compatible base URL over HTTPS with the API key header
