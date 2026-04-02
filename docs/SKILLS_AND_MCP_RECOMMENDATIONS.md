# AI Interview Room — Skills & MCP Recommendations

Recommendations to level up Cursor’s capabilities for this repo: project-specific **skills**, **Cursor rules**, and **MCP servers** aligned with the stack and [roadmap.md](roadmap.md).

---

## 1. Project skills (`.cursor/skills/`)

Create these in the **project** so anyone cloning the repo gets the same guidance.

### 1.1 `ai-interview-pipeline`

**Purpose:** Teach the agent the STT → LLM → TTS flow, WebSocket contract, and humanization rules so edits stay consistent.

**Trigger:** Working on `backend/routers/ws.py`, providers, or frontend interview/audio services.

**Description (for SKILL.md):**
> Orchestrates the real-time interview pipeline: WebSocket audio streaming, STT (faster-whisper / cloud), LLM (Groq/local-cpp), sentence-level TTS (Kokoro). Use when modifying the pipeline, adding providers, or debugging latency/VAD/turn-taking.

**Contents to include:**
- Message types: `speech-start`, `speech-end`, `interview-start`, `interview-end`; outgoing `status`, `transcript`, `ai-response`, `tts-audio` + binary chunk.
- Humanization: 2s thinking room, 300–800ms response delay, barge-in by cancelling `current_response_task`.
- Profiler stats: `stt_ms`, `llm_ttft_ms`, `llm_total_ms`, `tts_total_ms`, `total_e2e_ms`.

### 1.2 `backend-fastapi-conventions`

**Purpose:** FastAPI + Pydantic + async patterns used in this backend.

**Trigger:** Editing `backend/**/*.py` (routers, services, config, providers).

**Description:**
> FastAPI backend with async SQLAlchemy, Pydantic schemas (camelCase aliases), app.state providers, and lifespan loading. Use when adding routes, changing config, or touching the database layer.

**Contents to include:**
- Config from `backend.config.settings` (Pydantic BaseSettings, env).
- Schemas in `backend.models.schemas` with `to_camel` alias; use `model_dump(by_alias=True)` for JSON.
- DB: `AsyncSessionFactory`, repositories; run migrations with Alembic.

### 1.3 `frontend-angular-signals`

**Purpose:** Angular 21 + Signals + RxJS + Material patterns used in the frontend.

**Trigger:** Editing `frontend/src/**/*.ts` or `*.html`.

**Description:**
> Angular 17+ with Signals and RxJS. Use when changing interview UI, WebSocket handling, or audio capture/playback services.

**Contents to include:**
- Prefer Signals for component state; RxJS for streams (WebSocket, audio).
- Services: `WebSocketService`, `AudioCaptureService`, `AudioPlaybackService`; connect to `/ws/audio` and handle binary + JSON messages.
- Match backend message types and camelCase.

### 1.4 `roadmap-phase5-phase6`

**Purpose:** Phase 5 (OAuth, Stripe, analytics) and Phase 6 (RAG, fine-tuning, multi-voice) so the agent suggests implementations that fit the roadmap.

**Trigger:** Planning or implementing auth, payments, feedback reports, RAG, or TTS personas.

**Description:**
> Implements roadmap items: Google OAuth, Stripe subscriptions, post-session analytics, RAG from job descriptions, fine-tuning on interview transcripts, multi-voice TTS. Use when scoping or implementing these features.

**Contents to include:**
- Phase 5: OAuth (e.g. Auth0 or Google OIDC), Stripe usage metering + tiers, “feedback report” data model and API.
- Phase 6: RAG pipeline (job description → context for prompt), fine-tuning dataset shape, TTS voice selection in config/UI.

---

## 2. Cursor rules (`.cursor/rules/`)

Short, file-scoped rules so the agent follows project conventions.

| File | Purpose |
|------|--------|
| `backend-python.mdc` | `globs: backend/**/*.py` — async/await, type hints, logging with `logger = logging.getLogger(__name__)`, no bare `except`. |
| `frontend-angular.mdc` | `globs: frontend/src/**/*.ts` — Signals for state, inject services, single-quote and printWidth 100 (per frontend Prettier). |
| `api-websocket.mdc` | `globs: backend/routers/ws.py`, `frontend/**/websocket*.ts`, `**/audio*.ts` — preserve message type contracts and error codes (`PROVIDERS_NOT_READY`, `STT_ERROR`, etc.). |

Keep each rule under ~50 lines with 1–2 concrete do/don’t examples.

---

## 3. MCP servers

Use MCP to give the agent direct access to databases, Git, and external APIs. Configure in **Cursor Settings → MCP** (or project/user `mcp.json`). Prefer env vars for secrets.

### 3.1 Already in use

- **Angular CLI MCP** (`frontend/.vscode/mcp.json`): `npx -y @angular/cli mcp` — Angular-specific tooling. Keep this.

### 3.2 Recommended additions

| MCP Server | Role | Why |
|------------|------|-----|
| **Stripe MCP** | Payments & subscriptions | Roadmap: Phase 5 Stripe integration. Use for products, prices, usage metering, and subscription flows. Configure via [Stripe MCP](https://docs.stripe.com/mcp) (OAuth or API key in env). |
| **PostgreSQL** | Schema & data | Backend uses Postgres (SQLAlchemy/Alembic). Use for schema inspection, ad-hoc queries, and migration reasoning. Options: community Postgres MCP (e.g. [mcpindex.net](https://mcpindex.net/en/mcpserver/modelcontextprotocol-server-postgres)) or Prisma MCP with a Postgres datasource. Point at `postgres_host`/`postgres_db` from config. |
| **Git** | Repo context | From [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers): read blame, diff, log. Helps when discussing history or refactors. |
| **Fetch / Web** | Live docs | Fetch Stripe docs, FastAPI/OpenAPI, Angular docs when implementing OAuth, webhooks, or new APIs. |
| **Filesystem** (optional) | Safe file ops | Reference implementation for constrained file access if you want the agent to read/write only under `backend/` or `frontend/src/` in a controlled way. |

### 3.3 Example `mcp.json` (project or user)

```json
{
  "mcpServers": {
    "angular-cli": {
      "command": "npx",
      "args": ["-y", "@angular/cli", "mcp"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/ai_interview"
      }
    },
    "stripe": {
      "url": "https://mcp.stripe.com",
      "transport": "streamableHttp"
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "env": {
        "GIT_REPO_PATH": "."
      }
    }
  }
}
```

Use env vars (e.g. `POSTGRES_URL`, `STRIPE_*`) instead of hardcoding secrets; reference them in your env docs.

---

## 4. Quick wins

1. **Add `.cursor/rules/`** with `backend-python.mdc` and `api-websocket.mdc` so WebSocket and backend changes stay consistent.
2. **Create the `ai-interview-pipeline` skill** so any refactor of `ws.py` or providers follows the existing pipeline and message contract.
3. **Enable Stripe MCP** when you start Phase 5 so the agent can use Stripe’s API and docs.
4. **Add a Postgres MCP** with a read-only or dev connection so the agent can reason about schema and migrations (Alembic, `Interview`, messages).

---

## 5. Summary

| Category | Suggestion |
|----------|------------|
| **Skills** | `ai-interview-pipeline`, `backend-fastapi-conventions`, `frontend-angular-signals`, `roadmap-phase5-phase6` |
| **Rules** | `backend-python.mdc`, `frontend-angular.mdc`, `api-websocket.mdc` |
| **MCP** | Keep Angular CLI; add Stripe, Postgres, Git; optional: Fetch, Filesystem |

If you want, I can draft the first skill (e.g. `ai-interview-pipeline`) and one rule (e.g. `api-websocket.mdc`) in the repo next.
