# AI Interview Room

How to run the full stack locally.

## Prerequisites

- **Node.js** (for Angular frontend)
- **Python 3.11+** (for FastAPI backend)
- **Docker & Docker Compose** (for Postgres and Redis)
- **Groq API key** (for LLM when `AI_BACKEND=groq`)

## 1. Clone and env

```bash
cd AI-Interview-Room
cp .env.example .env
```

Edit `.env` and set at least:

- `GROQ_API_KEY=your_groq_api_key_here` (get one at [console.groq.com](https://console.groq.com))

## 2. Start Postgres and Redis

```bash
docker compose up -d
```

Check they’re up: `docker compose ps`. Defaults: Postgres on `localhost:5432`, Redis on `localhost:6379`.

## 3. Backend (FastAPI)

From the **project root** (so `backend` is the package name):

```bash
# Create a venv and install deps (first time)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r backend/requirements.txt

# Run the server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Backend will:

- Load `.env`
- Connect to Postgres and Redis
- Load AI providers (STT, LLM, TTS). With `AI_BACKEND=groq` it uses Groq for LLM; local STT (faster-whisper) and TTS (Kokoro) load on startup (can take a minute).

API: [http://localhost:8000](http://localhost:8000) — docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## 4. Frontend (Angular)

In a **second terminal**:

```bash
cd frontend
npm install
npm start
# or: ng serve
```

App: [http://localhost:4200](http://localhost:4200). It talks to the backend at `localhost:8000` (or your configured API/WS URL).

## 5. Run the interview

1. Open [http://localhost:4200](http://localhost:4200).
2. Start an interview (position, difficulty, focus areas).
3. Allow mic access; speak. The pipeline is: mic → VAD → WebSocket → STT → LLM (Groq) → TTS → playback.

## Quick recap

| Step | Command | Where |
|------|---------|--------|
| DB + Redis | `docker compose up -d` | Project root |
| Backend | `uvicorn backend.main:app --host 0.0.0.0 --port 8000` | Project root (with venv active) |
| Frontend | `npm start` | `frontend/` |

## Troubleshooting

- **“Providers not ready”** — Wait for backend startup (STT/TTS models load). Check logs.
- **DB connection errors** — Ensure `docker compose up -d` and `.env` matches `POSTGRES_*` (defaults: user `postgres`, password `changeme`, db `ai_interview`).
- **CORS** — Backend `CORS_ORIGINS` must include the frontend origin (default `http://localhost:4200`).
