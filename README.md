# AI Server

A FastAPI-based AI tutor server utilizing `uv` for python dependency management and execution.

---

## Requirements

### 1. System Requirements
- **Python**: `>=3.12` (Python 3.12+ is required)
- **Dependency Manager**: [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip` / `virtualenv`

### 2. Environment Variables (`.env`)
The server reads configuration from a `.env` file at the root. You can copy the example:
```bash
cp .env.example .env
```

The configuration variables are:
- `AI_SERVICE_SECRET`: Shared static secret used to authenticate incoming service-to-service requests (minimum 32-character string recommended).
- `SESSION_SIGNING_SECRET`: HS256 secret key used to sign and verify session JWTs.
- `SESSION_TOKEN_TTL_SECONDS`: Expiry duration for JWT tokens in seconds (defaults to `300`).
- `GEMINI_API_KEY`: API key for Google Gemini model access.
- `OPENAI_API_KEY`: API key for OpenAI model access.
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude model access.

### 3. Core Dependencies
The project lists the following core libraries in [pyproject.toml](pyproject.toml):
- `fastapi`: Web framework
- `uvicorn[standard]`: ASGI web server
- `pydantic` & `pydantic-settings`: Schema definition and environment configuration
- `sse-starlette`: Server-Sent Events (SSE) streaming support
- `httpx`: Async HTTP client
- `pyjwt[crypto]`: JSON Web Token signing & verification
- `anthropic`: Anthropic Claude API client
- `openai`: OpenAI API client
- `google-genai`: Google Gemini API client

### 4. Development Dependencies (Optional)
- `pytest` & `pytest-asyncio`: Testing framework and async support
- `ruff`: Linter and code formatter
- `mypy`: Static type checker

---

## Setup & Installation

Sync your local environment and install all core + development dependencies:
```bash
uv sync --all-extras
```

*(Alternatively, if using standard python venv)*:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

---

## How to Run the Server

### Option A: Using `uv` (Recommended)
Run the development server with hot-reloading:
```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option B: Using the Virtual Environment Directly
```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option C: Activating the Virtual Environment First
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, the server is available at **`http://127.0.0.1:8000`**. You can verify that the healthcheck is running by visiting:
[http://127.0.0.1:8000/v1/healthz](http://127.0.0.1:8000/v1/healthz)

---

## Running Quality Checks

### Run Tests
```bash
uv run pytest
```

### Run Linter
```bash
uv run ruff check .
```

### Run Type Checker
```bash
uv run mypy app
```
