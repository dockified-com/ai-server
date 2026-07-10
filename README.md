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

## V1 Tutoring Agents

Generation/authoring agents (`outline`, `generate-blocks`, `agent-edit`) are **omitted** from the default registry for pilot deploys. Registered agents:

| Agent | Mode | Endpoint | Purpose |
| --- | --- | --- | --- |
| `tutor_open` | stream | `POST /v1/reason` | Session open: greet, course name, ask preferred name (no teaching) |
| `pre_assess` | stream | `POST /v1/reason` | Short pre-assessment dialogue; propose beginner/intermediate/advanced |
| `socratic` | stream | `POST /v1/reason` | Socratic code hints (no full solutions) |
| `understanding-check` | stream | `POST /v1/reason` | Rubric evaluation; emits signed `result` event |
| `ask` | stream | `POST /v1/reason` | Course-context Q&A; emits signed `result` event |
| `final_clarify` | stream | `POST /v1/reason` | Final-eval wording-only clarify (no hints/code/strategy) |
| `code-eval` | json | `POST /v1/run` | Pass/fail code verdict JSON |
| `tts` | stream (placeholder) | `POST /v1/speak` | Session mint only for TTS; audio via `/v1/speak`, not text generation |

Message builders live in `app/runtime/reasoning.py` (`build_user_message`). Server-sealed fields come from JWT `server_context`; turn data comes from request `client_context`.

---

## Next → mint session → browser SSE to `/v1/reason`

Tutoring text is never called with long-lived API keys from the browser. Flow:

1. **Next.js (server)** mints a short-lived session JWT:
   ```http
   POST /v1/session
   Authorization: Bearer <AI_SERVICE_SECRET>
   Content-Type: application/json

   {
     "agent": "tutor_open",
     "server_context": {
       "courseTitle": "Intro Python",
       "lessonTitle": "Variables"
     }
   }
   ```
   Response: `{ "session_token": "<jwt>", "expires_in": 300 }`.  
   The JWT embeds `agent` + `server_context` (problem prompt, rubric, RAG chunks, etc.) and is signed with `SESSION_SIGNING_SECRET`.

2. **Browser** streams tokens with that token (no service secret):
   ```http
   POST /v1/reason
   Authorization: Bearer <session_token>
   Content-Type: application/json

   {
     "client_context": {
       "message": "Hi, call me Alex"
     }
   }
   ```

3. **SSE events** from `/v1/reason`:
   - `event: token` — text chunk (`data` is the raw token string)
   - `event: result` — optional signed JWT payload (currently `understanding-check` and `ask` only)
   - `event: done` — stream complete
   - `event: error` — model/runtime failure (`data`: `AI temporarily unavailable`)

4. **Speech (optional):** Next mints a session with `"agent": "tts"`, then the browser (or Next) calls `POST /v1/speak` with the session token and text. Hitting `/v1/reason` with a `tts` session completes with `done` only (no model call).

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
