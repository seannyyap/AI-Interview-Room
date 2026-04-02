# Cursor configuration for AI Interview Room

## MCP servers (`mcp.json`)

- **angular-cli** — Angular tooling (e.g. generate, analyze). No env required.
- **postgres** — Database schema and queries. Set `DATABASE_URL` (or the variable the server expects) in your environment before starting Cursor, e.g. `postgresql://postgres:changeme@localhost:5432/ai_interview`, so the Postgres MCP inherits it.
- **stripe** — Stripe API (Phase 5). Configure via [Stripe MCP](https://docs.stripe.com/mcp); you may need to sign in or set an API key in Cursor’s MCP settings.
- **git** — Repo history and diff. Uses current workspace as `GIT_REPO_PATH`; no secrets needed.

After changing `mcp.json` or env vars, restart Cursor so MCP servers reload.

## Rules (`.cursor/rules/*.mdc`)

Apply when editing matching files:

- `backend-python.mdc` — backend Python
- `frontend-angular.mdc` — frontend TypeScript
- `api-websocket.mdc` — WebSocket router and frontend WS/audio services

## Skills (`.cursor/skills/*`)

Loaded automatically when relevant:

- **ai-interview-pipeline** — STT → LLM → TTS, WebSocket contract, humanization
- **backend-fastapi-conventions** — Config, schemas, DB, lifespan
- **frontend-angular-signals** — Signals, RxJS, WS/audio services
- **roadmap-phase5-phase6** — OAuth, Stripe, RAG, fine-tuning, multi-voice
