# AI Interview Room — Learning Roadmap

> **Goal:** You're a software engineer learning to become an AI engineer.  
> This roadmap starts with what you already know (web dev, APIs, databases) and progressively introduces AI concepts — each phase builds on the last.  
> **No vibe coding.** Every step has a *why*, a *what to learn*, and a *what to build*.

> **Product Target:** B2C SaaS — AI mock interviewer for job seekers ($19–49/month).  
> Competitors: Edesy AI, Pramp, Interviewing.io. Your edge: **local-first AI with optional cloud**, no data leaves the user's machine unless they choose it.

### Your Hardware

| Component | Spec |
|---|---|
| **CPU** | Ryzen 5 5600 — 6 cores / 12 threads, Zen 3 |
| **GPU** | RX 7800 XT — 16GB VRAM, AMD RDNA 3 |
| **Strategy** | STT + TTS on **CPU** · LLM on **GPU via Vulkan** |

> Your 16GB AMD GPU is excellent for LLM inference via llama.cpp's Vulkan backend — more VRAM than most NVIDIA consumer cards. STT and TTS are lightweight enough for your 6-core CPU.

### Architecture — Pluggable AI Backends

> **Key design decision:** Every AI service (STT, LLM, TTS) is built behind an abstract interface from day one. You develop with local models, but can swap to cloud APIs (Deepgram, OpenAI, ElevenLabs) for production without touching business logic.

```
┌─────────────────────────────────────────────────────────────┐
│                   Angular Frontend                          │
│          Audio Capture · Interview UI · Dashboard           │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI Orchestrator                        │
│        Session Mgmt · Conversation · Routing                │
└────┬─────────────────┬──────────────────┬───────────────────┘
     │                 │                  │
┌────▼─────┐    ┌──────▼──────┐    ┌──────▼──────┐
│ STT      │    │ LLM         │    │ TTS         │
│ Provider │    │ Provider    │    │ Provider    │
├──────────┤    ├─────────────┤    ├─────────────┤
│ Local:   │    │ Local:      │    │ Local:      │
│ Whisper  │    │ llama.cpp   │    │ Piper       │
│ Cloud:   │    │ Cloud:      │    │ Cloud:      │
│ Deepgram │    │ OpenAI/     │    │ ElevenLabs  │
│          │    │ Anthropic   │    │             │
└──────────┘    └─────────────┘    └─────────────┘
                        │
              ┌─────────▼─────────┐
              │   PostgreSQL      │
              │   Redis · MinIO   │
              └───────────────────┘
```

### Engineering Principles (Applied in Every Phase)

These four pillars are woven into every phase — not bolted on at the end:

| Principle | What It Means in This Project |
|---|---|
| 🔒 **Security** | Validate all inputs. Sanitize audio/text. Auth on every endpoint. Never trust the client. |
| ⚡ **Performance** | Measure latency at every stage. Profile before optimizing. Set latency budgets. |
| 📈 **Scalability** | Design stateless where possible. Decouple components. Plan for session concurrency. |
| 🔧 **Maintainability** | Clean interfaces between modules. Type everything. Test at boundaries. Document decisions. |

---

## How to Use This Roadmap

- Work through phases **in order** — each depends on the previous one
- Each phase has **learning resources** → **concepts to understand** → **what to build** → **engineering checklist**
- Don't move to the next phase until you can explain the current one to someone else
- Commit after each phase — your git history becomes your learning journal

---

## Phase 0 — Project Foundation (You Know This)

> **Skill level:** Software Engineer  
> **Time estimate:** 1–2 days  
> **Goal:** Set up the monorepo, tooling, and dev environment with good engineering foundations

### What to Do

1. **Initialize the monorepo structure**
   ```
   AI-Interview-Room/
   ├── apps/
   │   └── frontend/           # Angular app (Phase 1)
   ├── services/
   │   └── ai-orchestrator/    # FastAPI app (Phase 2)
   ├── packages/
   │   ├── shared-types/       # Shared TypeScript/Python schemas
   │   └── prompts/            # Interview prompt templates
   ├── infra/
   │   └── docker/             # Dockerfiles + compose
   ├── docs/                   # Your notes and learnings
   ├── .gitignore
   ├── README.md
   └── ROADMAP.md              # This file
   ```

2. **Set up Docker + Docker Compose**
   - Install Docker Desktop
   - Write a base `docker-compose.yml` that you'll extend in each phase

3. **Set up Python environment for the backend**
   - Install Python 3.11+
   - Learn `uv` for dependency management
   - Create a virtual environment for `services/ai-orchestrator/`
   - Pin all dependency versions from day one (`uv.lock`)

4. **Set up Node environment for the frontend**
   - Node 20+ with npm
   - Install Angular CLI globally: `npm install -g @angular/cli`
   - Initialize Angular 17+ with standalone components: `ng new frontend --standalone --style=scss --routing --ssr=false`
   - Add Angular Material: `ng add @angular/material`

5. **Install Vulkan SDK** (for Phase 4 later)
   - Download from [vulkan.lunarg.com](https://vulkan.lunarg.com/)
   - Verify with `vulkaninfo` — confirms your RX 7800 XT is detected
   - This is a one-time setup for your AMD GPU

### Engineering Checklist — Phase 0

| Principle | Action |
|---|---|
| 🔒 Security | Add `.env.example` with placeholder secrets. Add `.env` to `.gitignore`. Never commit secrets. |
| 🔒 Security | Set up `pre-commit` hooks: lint + secret scanning (`detect-secrets` or `gitleaks`) |
| ⚡ Performance | N/A for this phase |
| 📈 Scalability | Structure as a monorepo — services are independently deployable from the start |
| 🔧 Maintainability | Set up linters: ESLint (frontend), Ruff (Python). Enforce from day one. |
| 🔧 Maintainability | Create `docs/decisions/` folder for ADRs (Architecture Decision Records) — document WHY you chose each tool |

---

## Phase 1 — Frontend: Angular UI + Audio Capture

> **Skill level:** Frontend Engineer  
> **Time estimate:** 5–7 days  
> **Goal:** Build the complete Angular UI with audio capture, WebSocket streaming, and a landing page

### What to Learn First

1. **Angular 17+ Fundamentals** (if rusty)
   - Standalone components (no NgModules needed)
   - Signals for reactive state management
   - `inject()` function for dependency injection
   - New control flow syntax (`@if`, `@for`, `@switch`)
   - Resource: [Angular.dev](https://angular.dev/)

2. **RxJS for Real-Time Streams**
   - `Subject`, `BehaviorSubject`, `Observable`
   - Operators: `switchMap`, `mergeMap`, `takeUntil`, `debounceTime`, `buffer`
   - Why RxJS is perfect for WebSocket audio streams
   - Resource: [RxJS Guide](https://rxjs.dev/guide/overview)

3. **Web Audio API**
   - What is an `AudioContext`?
   - What are `AudioWorkletNode` and `AudioWorkletProcessor`?
   - How does audio sampling work? (sample rate, bit depth, PCM)
   - Resource: [MDN Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

4. **MediaStream API**
   - `navigator.mediaDevices.getUserMedia()` — how to get mic access
   - What is a `MediaStream` vs a `MediaStreamTrack`?
   - Resource: [MDN MediaStream](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream)

5. **WebSocket for Audio Streaming**
   - Sending binary data (ArrayBuffer) over WebSocket
   - Why WebSocket and not HTTP for real-time audio?
   - Buffering strategies: how many milliseconds of audio per chunk?

### Key Concepts to Understand

| Concept | Why It Matters |
|---|---|
| **PCM (Pulse Code Modulation)** | Raw audio format. STT models consume raw audio, not MP3. |
| **Sample Rate (16kHz vs 44.1kHz)** | Whisper expects 16kHz mono. Browser captures at 44.1kHz or 48kHz. You need to downsample. |
| **Audio Chunking** | You can't send a 30-minute audio blob. You stream 100-500ms chunks in real time. |
| **Float32 vs Int16** | Web Audio outputs Float32 samples (-1.0 to 1.0). Whisper expects Int16 or Float32 at 16kHz. |
| **Angular Signals vs RxJS** | Use Signals for simple UI state (loading, connection status). Use RxJS for complex async streams (WebSocket, audio). |

### What to Build

1. **Landing Page** (`/`)
   - Hero section: "Practice interviews with AI"
   - Feature highlights, pricing teaser, CTA button
   - SEO-optimized: proper meta tags, structured data
   - Use Angular Material components for a polished look

2. **Interview Room Page** (`/interview`)
   - Start/Stop button, live audio waveform visualizer, transcript area (empty for now)
   - Use Angular Material or Spartan UI components

3. **Audio Capture Service** (`services/audio-capture.service.ts`)
   - Use `AudioWorkletProcessor` to capture raw PCM from the mic
   - Downsample from 48kHz → 16kHz in the worklet
   - Output Float32Array chunks (every ~250ms)
   - Expose as an RxJS Observable: `audioChunks$: Observable<Float32Array>`

4. **WebSocket Service** (`services/websocket.service.ts`)
   - Connect to `ws://localhost:8000/ws/audio`
   - Stream audio chunks as binary messages
   - Receive text messages back (transcripts, AI responses)
   - Connection state as a Signal: `connectionState: Signal<ConnectionState>`
   - Handle reconnection logic with RxJS `retryWhen`

5. **Audio Playback Service** (`services/audio-playback.service.ts`)
   - Receive TTS audio chunks from the server
   - Queue and play them using Web Audio API
   - Handle seamless playback of streamed chunks (no gaps or clicks)

6. **Dashboard Page** (`/dashboard`) — skeleton for now
   - Interview history list (mock data)
   - Score summaries (mock data)
   - This gets real data in Phase 3

### Engineering Checklist — Phase 1

| Principle | Action |
|---|---|
| 🔒 Security | Request **only** microphone permission — never request camera unless needed later |
| 🔒 Security | Validate WebSocket URL from environment config, not hardcoded. Use `wss://` in production. |
| 🔒 Security | Sanitize any text you render from the server (XSS prevention). Angular's built-in sanitizer handles most cases. |
| ⚡ Performance | Downsample in the `AudioWorkletProcessor` (runs on audio thread, not main thread) — never block the UI thread |
| ⚡ Performance | Tune chunk size: 250ms = good balance between latency and overhead. Measure round-trip time. |
| ⚡ Performance | Lazy-load the interview room and dashboard routes — the landing page should load instantly |
| 📈 Scalability | Abstract the WebSocket client behind an Angular service — you may switch to a different transport later |
| 📈 Scalability | Design the audio capture as a standalone service — it should work with any backend |
| 🔧 Maintainability | Type all WebSocket message formats with TypeScript interfaces (`AudioChunkMessage`, `TranscriptMessage`) |
| 🔧 Maintainability | Add a connection state machine: `DISCONNECTED → CONNECTING → CONNECTED → STREAMING → ERROR` |
| 🔧 Maintainability | Use Angular's `environment.ts` files for configuration (API URLs, feature flags) |

### Checkpoint
> ✅ You should be able to: Open the page, click "Start", speak into your mic, and see raw PCM chunks being sent over WebSocket (check browser DevTools → Network → WS tab). No backend needed yet — just verify the client sends binary data. The landing page should look like a real product.

---

## Phase 2 — Backend: FastAPI + WebSocket Server + Service Interfaces

> **Skill level:** Backend Engineer  
> **Time estimate:** 3–5 days  
> **Goal:** Build a FastAPI server with pluggable AI service interfaces and session management

### What to Learn First

1. **FastAPI WebSocket handling**
   - `@app.websocket("/ws/audio")` endpoint
   - Receiving binary data from WebSocket in Python
   - Async generators for streaming responses
   - Resource: [FastAPI WebSockets docs](https://fastapi.tiangolo.com/advanced/websockets/)

2. **Python Abstract Base Classes & Protocols**
   - `Protocol` (structural subtyping) for service interfaces
   - Why this matters: swap local models for cloud APIs without changing callers
   - Resource: [Python typing — Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)

3. **Audio in Python**
   - `numpy` for audio array manipulation
   - Understanding `numpy.frombuffer(data, dtype=np.float32)`
   - Saving raw PCM to a `.wav` file with the `wave` module (for debugging)

### What to Build

1. **Pluggable Service Interfaces** (`services/interfaces.py`) — **BUILD THIS FIRST**
   ```python
   from typing import Protocol, AsyncIterator

   class STTProvider(Protocol):
       async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str: ...

   class LLMProvider(Protocol):
       async def generate(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...

   class TTSProvider(Protocol):
       async def synthesize(self, text: str) -> bytes: ...
   ```
   - Every AI service coded in Phase 4 will implement these interfaces
   - For now, create `MockSTTProvider`, `MockLLMProvider`, `MockTTSProvider` that return dummy data

2. **WebSocket Endpoint** (`routers/ws.py`)
   - Accept WebSocket connections
   - Receive binary audio chunks
   - Log chunk sizes and timestamps (proves the pipeline works)
   - Pass audio through `STTProvider` → `LLMProvider` → `TTSProvider` (mocked)
   - Send back JSON responses: `{"type": "transcript", "text": "..."}`

3. **Audio Buffer Service** (`services/audio_buffer.py`)
   - Accumulate incoming chunks into a rolling buffer
   - When buffer reaches N seconds of audio, yield it for processing
   - This prepares you for feeding audio into faster-whisper in Phase 4

4. **Session Manager** (`services/session.py`)
   - Track active interview sessions (in-memory dict for now, Redis in Phase 3)
   - Each WebSocket connection = one session
   - Store session metadata: start time, state, conversation history

5. **REST API Endpoints** (`routers/api.py`)
   - `GET /api/interviews` — list past interviews (mock data for now)
   - `GET /api/interviews/{id}` — interview detail with transcript
   - `POST /api/interviews` — start a new interview
   - `GET /api/health` — health check endpoint

6. **Configuration** (`config.py`)
   - Pydantic `BaseSettings` for all config
   - `AI_BACKEND: Literal["local", "cloud"]` — controls which provider loads
   - Model paths, API keys, feature flags — all from env vars

7. **Docker Compose**
   - `ai-orchestrator` service with hot-reload (`uvicorn --reload`)
   - Expose port 8000
   - Volume mount your code for development

### Engineering Checklist — Phase 2

| Principle | Action |
|---|---|
| 🔒 Security | **Validate audio chunks**: check size limits (reject chunks > 1MB), check expected dtype/format |
| 🔒 Security | **Rate limit** WebSocket connections: max 1 session per IP for now. Prevents abuse. |
| 🔒 Security | **CORS**: configure `allowed_origins` explicitly. Never use `*` in production. |
| 🔒 Security | Set up `config.py` using Pydantic `BaseSettings` — all config from env vars, validated at startup |
| ⚡ Performance | Use `asyncio` properly — never block the event loop. Audio processing should be `run_in_executor` if CPU-bound. |
| ⚡ Performance | Add timing logs: `[WS] chunk received at {ts}, size={n} bytes` — this becomes your baseline for latency analysis |
| 📈 Scalability | Service interfaces (Protocol) let you swap backends without touching callers |
| 📈 Scalability | Design WebSocket handlers to be **stateless** — all session state lives in the session manager, not in handler locals |
| 🔧 Maintainability | Use Pydantic models for **all** WebSocket message types — both incoming and outgoing |
| 🔧 Maintainability | Structure: `routers/` (endpoints) → `services/` (business logic) → `models/` (Pydantic schemas). Clear separation. |
| 🔧 Maintainability | Write your first integration test: WebSocket client sends dummy audio → server responds. Use `pytest` + `httpx`. |

### Checkpoint
> ✅ You should be able to: Open the Angular frontend, speak, see audio chunks arrive at the backend (logged), and receive dummy text responses displayed in the transcript area. **Full round-trip over WebSocket, no AI yet — but the service interfaces are ready for real models.**

---

## Phase 3 — Data Layer & Storage

> **Skill level:** Software Engineer (familiar)  
> **Time estimate:** 3–5 days  
> **Goal:** Persist interviews, transcripts, recordings, user accounts, and wire the dashboard with real data

### What to Learn First

1. **SQLAlchemy 2.0 with async**
   - Declarative models with `mapped_column`
   - Async session factory with `asyncpg`
   - Resource: [SQLAlchemy 2.0 tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

2. **Alembic for migrations**
   - Auto-generate migrations from model changes
   - Never modify the database schema manually

3. **Redis fundamentals**
   - Key-value storage, TTL, Pub/Sub
   - Why Redis for sessions: fast, ephemeral, supports TTL expiry

### What to Build

1. **PostgreSQL Schema** (via SQLAlchemy models + Alembic migrations)
   - `users` table: id, email, hashed_password, role, created_at, deleted_at
   - `interviews` table: id, user_id, position, status, config (JSON), started_at, ended_at
   - `messages` table: id, interview_id, role (user/ai), content, timestamp
   - `scores` table: id, interview_id, criteria, score, reasoning, created_at

2. **Repository Layer** (`repositories/`)
   - `UserRepository` — CRUD for users
   - `InterviewRepository` — CRUD for interviews + messages
   - `ScoreRepository` — CRUD for scores
   - Repository pattern: don't scatter SQL across services

3. **Redis Integration**
   - Session state (active interviews) with TTL
   - Swap in-memory session manager from Phase 2 for Redis-backed one
   - Rate limiting token bucket

4. **MinIO for Object Storage**
   - Store audio recordings (full interview WAV/opus)
   - Store exported transcripts or reports
   - Pre-signed URLs for secure download

5. **Wire the Dashboard**
   - Connect Angular dashboard page to real REST endpoints
   - Display interview history from PostgreSQL
   - Display score summaries

6. **Docker Compose Update**
   - Add PostgreSQL, Redis, MinIO containers
   - Persistent volumes for data

### Engineering Checklist — Phase 3

| Principle | Action |
|---|---|
| 🔒 Security | **Hash passwords** with `bcrypt` or `argon2` — never store plaintext. |
| 🔒 Security | **Parameterized queries only** — use SQLAlchemy ORM. Never string-format SQL. |
| 🔒 Security | **Encrypt audio at rest** in MinIO (SSE-S3 encryption). Interview recordings are sensitive HR data. |
| 🔒 Security | **Pre-signed URLs** for file downloads — time-limited (15 min), per-user. |
| 🔒 Security | **PII handling** — candidate names, transcripts, scores are PII. Implement soft-delete (`deleted_at`). Plan for GDPR from day one. |
| ⚡ Performance | **Index** frequently queried columns: `interviews.user_id`, `messages.interview_id`, `interviews.status`. |
| ⚡ Performance | Use connection pooling (`asyncpg` + SQLAlchemy async) — don't open a new DB connection per request. |
| 📈 Scalability | MinIO is S3-compatible — swap for real S3 in production with zero code changes. |
| 📈 Scalability | Repository pattern makes it easy to add caching or read replicas later. |
| 🔧 Maintainability | **Alembic migrations** — every schema change is versioned and reversible. |
| 🔧 Maintainability | Write DB seed scripts for development/testing data. |

### Checkpoint
> ✅ You should be able to: Complete a mock interview → see it stored in PostgreSQL → view it on the Angular dashboard → download the audio recording from MinIO. Data persists across restarts.

---

## Phase 4 — AI Models: STT, LLM & TTS 🧠

> **Skill level:** Entering AI territory  
> **Time estimate:** 10–14 days  
> **Goal:** Implement real AI providers (local + cloud) behind the service interfaces you built in Phase 2

This is the longest and most important phase. Take your time with the learning sections.

### Part A: Speech-to-Text (STT) — 4–5 days

#### What to Learn First (CRITICAL)

1. **What is a Machine Learning Model?**
   - A model is a file containing learned numerical weights (parameters)
   - You download a pretrained model — you don't train it yourself
   - Models have specific input/output formats you must match
   - Resource: [3Blue1Brown — Neural Networks](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi) (watch at least episodes 1-3)

2. **What is Whisper?**
   - OpenAI's speech recognition model (open-source)
   - Takes: audio waveform (16kHz, mono, float32) → Returns: text with timestamps
   - Model sizes: tiny, base, small, medium, large-v3 (bigger = more accurate = slower)
   - Resource: [Whisper paper (read the abstract + Section 2)](https://arxiv.org/abs/2212.04356)

3. **What is faster-whisper?**
   - A reimplementation of Whisper using CTranslate2 (optimized inference engine)
   - 4x faster than the original, lower memory usage
   - Same accuracy, same models, just faster execution
   - Resource: [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)

4. **What is CTranslate2?**
   - A C++ inference engine that converts models to an optimized format
   - Supports quantization: float32 → float16 → int8 (smaller, faster, slightly less accurate)
   - This is your first encounter with **model optimization** — a core AI engineering skill
   - Resource: [CTranslate2 docs — quantization](https://opennmt.net/CTranslate2/quantization.html)

5. **CPU Inference on Your Ryzen 5 5600**
   - 6 cores / 12 threads — set `OMP_NUM_THREADS=6` (use physical cores, not logical)
   - faster-whisper `base` + int8 on your CPU = real-time transcription
   - CTranslate2 uses OpenMP for CPU parallelism — thread tuning matters

#### Key Concepts

| Concept | Why It Matters |
|---|---|
| **Model Loading** | Models are loaded into RAM once at startup. Slow (5-30s). Never reload per request. |
| **Inference** | Running input through a model to get output. Every audio → text call is inference. |
| **VAD (Voice Activity Detection)** | Detects speech vs silence. faster-whisper has built-in Silero VAD. Critical for knowing when to transcribe. |
| **Quantization** | Reducing precision (float32 → int8) for less memory and faster speed. **Essential on CPU.** |

#### What to Build

1. **Local STT Provider** (`providers/local_stt.py`)
   - Implements `STTProvider` protocol from Phase 2
   - Load faster-whisper model once at startup (singleton):
     ```python
     from faster_whisper import WhisperModel
     model = WhisperModel("base", device="cpu", compute_type="int8")
     ```
   - Enable VAD filtering: `vad_filter=True`

2. **Cloud STT Provider** (`providers/cloud_stt.py`)
   - Implements the same `STTProvider` protocol
   - Uses Deepgram or Google Cloud Speech-to-Text API
   - Same interface, different backend — this is the power of your Phase 2 design

3. **Provider Factory** (`providers/__init__.py`)
   - Reads `AI_BACKEND` from config
   - Returns local or cloud provider based on config

#### STT Experiments (DO THESE — they build intuition)

```python
# Experiment 1: Compare model sizes on your Ryzen 5 5600
for size in ["tiny", "base", "small"]:
    model = WhisperModel(size, device="cpu", compute_type="int8")
    segments, info = model.transcribe("test_audio.wav")
    # Measure: time, accuracy, RAM usage
    # Expected: tiny ~1s, base ~3s, small ~6s for 10s audio

# Experiment 2: Compare compute types on CPU
for ct in ["float32", "int8"]:
    model = WhisperModel("base", device="cpu", compute_type=ct)
    # int8 should be ~2x faster than float32 on CPU

# Experiment 3: VAD impact (CRITICAL — saves processing time)
segments, _ = model.transcribe("audio.wav", vad_filter=True)
segments, _ = model.transcribe("audio.wav", vad_filter=False)
# VAD skips silence → huge speed gain on CPU

# Experiment 4: Thread count on your 6-core Ryzen
import os
for threads in ["2", "4", "6", "8"]:
    os.environ["OMP_NUM_THREADS"] = threads
    # Reload model and measure. Sweet spot is likely 5 or 6.
```

---

### Part B: LLM Integration — 4–5 days 🧠🧠

#### What to Learn First (Spend at Least 2-3 Days Here)

1. **What is an LLM?**
   - A model trained on massive text data that predicts the next token
   - It doesn't "understand" — it's very good at pattern matching and generation
   - Resource: [Andrej Karpathy — Intro to LLMs (1hr)](https://www.youtube.com/watch?v=zjkBMFhNj_g)

2. **What are Tokens?**
   - LLMs process **tokens** (subword pieces), not words
   - "interviewing" → ["interview", "ing"] (2 tokens)
   - Context window = max tokens the model can see at once (4K, 8K, 32K, 128K)
   - Resource: [OpenAI Tokenizer tool](https://platform.openai.com/tokenizer)

3. **What is llama.cpp?**
   - C/C++ LLM inference engine, runs on CPU and GPU (including **AMD GPUs via Vulkan**)
   - Uses GGUF format — quantized model files from HuggingFace
   - `llama-cpp-python` = Python bindings
   - Resource: [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)

4. **What is Vulkan? (Critical for Your Setup)**
   - Cross-platform GPU API — works with AMD, NVIDIA, Intel
   - llama.cpp uses Vulkan to offload matrix multiplication to your RX 7800 XT
   - Build `llama-cpp-python` with Vulkan:
     ```powershell
     $env:CMAKE_ARGS="-DGGML_VULKAN=on"
     pip install llama-cpp-python --force-reinstall --no-cache-dir
     ```
   - Verify: look for `ggml_vulkan: Found 1 Vulkan device: AMD Radeon RX 7800 XT`

5. **What is Quantization (for LLMs)?**
   - Float16: 7B model ≈ 14GB VRAM
   - Q4_K_M: 7B model ≈ 4.5GB VRAM — fits easily in your 16GB
   - Your 7800 XT can also run 14B models at Q4

6. **Prompt Engineering**
   - System prompt = "You are an HR interviewer..."
   - Chat templates differ per model (Qwen, Llama, Mistral)
   - Resource: [Prompt Engineering Guide](https://www.promptingguide.ai/)

7. **Streaming Generation**
   - Get tokens one-by-one instead of waiting for the full response
   - Essential for real-time: start TTS before the LLM finishes

#### Key Concepts

| Concept | Why It Matters |
|---|---|
| **Temperature** | Controls randomness. 0.0 = deterministic, 1.0 = creative. For interviews: 0.3-0.7. |
| **Top-p / Top-k** | Alternative randomness controls. Top-p=0.9 is a good default. |
| **Context Window** | The LLM only "sees" the last N tokens. Manage conversation history to fit. |
| **System Prompt** | Defines the AI persona. This is where you make it an interviewer. |
| **n_gpu_layers** | How many layers to offload to GPU. Use `-1` for all layers. |
| **GGUF** | Model file format for llama.cpp. Download from HuggingFace. |

#### What to Build

1. **Download a Model**
   - HuggingFace → `Qwen2.5-7B-Instruct-GGUF` → `Q4_K_M` variant (~4.5GB)
   - Store in `models/` directory (git-ignored)

2. **Local LLM Provider** (`providers/local_llm.py`)
   - Implements `LLMProvider` protocol from Phase 2
   - Load model once at startup:
     ```python
     from llama_cpp import Llama
     model = Llama(
         model_path="models/qwen2.5-7b-instruct-q4_k_m.gguf",
         n_gpu_layers=-1,    # ALL layers on RX 7800 XT
         n_threads=6,         # CPU threads for your Ryzen 5
         n_ctx=4096,
         verbose=True,
     )
     ```
   - Stream tokens via async generator

3. **Cloud LLM Provider** (`providers/cloud_llm.py`)
   - Same `LLMProvider` protocol
   - Uses OpenAI API or Anthropic API
   - Same interface, cloud backend

4. **Interview Prompt System** (`packages/prompts/`)
   - System prompt for AI interviewer persona
   - Store prompts in versioned files, not inline strings
   - Start simple: "You are a technical interviewer for a software engineering position..."

5. **Conversation Manager** (`services/conversation.py`)
   - Maintain conversation history per session
   - Handle context window management (truncate old messages if too long)

#### LLM Experiments

```python
# Experiment 1: Verify Vulkan works
model = Llama("models/qwen2.5-7b-instruct-q4_k_m.gguf", n_gpu_layers=-1, verbose=True)
# Look for: "ggml_vulkan: Found 1 Vulkan device: AMD Radeon RX 7800 XT"

# Experiment 2: GPU vs CPU speed
model_gpu = Llama(model_path, n_gpu_layers=-1, n_threads=6)  # ~20-40 tok/s
model_cpu = Llama(model_path, n_gpu_layers=0, n_threads=6)    # ~5-8 tok/s

# Experiment 3: 7B vs 14B on your GPU
# Both fit in 16GB. Compare quality vs speed.

# Experiment 4: Temperature impact
for temp in [0.0, 0.3, 0.5, 0.7, 1.0]:
    response = model.create_completion(prompt, temperature=temp)
```

---

### Part C: Text-to-Speech (TTS) — 2–3 days

#### What to Learn First

1. **How does TTS work?**
   - Text → linguistic analysis → acoustic model → audio waveform
   - Resource: [Piper TTS docs](https://github.com/rhasspy/piper)

2. **Streaming TTS**
   - Don't wait for the LLM to finish — TTS **sentence by sentence**
   - This is called **sentence-level streaming** — key for low latency

#### What to Build

1. **Local TTS Provider** (`providers/local_tts.py`)
   - Implements `TTSProvider` protocol
   - Load Piper voice model at startup
   - Function: `text → audio bytes (PCM)`
   - Implement sentence-level processing

2. **Cloud TTS Provider** (`providers/cloud_tts.py`)
   - Same `TTSProvider` protocol
   - Uses ElevenLabs or Google Cloud TTS API

3. **Interrupt Handling (Barge-In)**
   - Stop TTS playback when user starts talking
   - Cancel pending TTS, start listening

### Engineering Checklist — Phase 4 (All Parts)

| Principle | Action |
|---|---|
| 🔒 Security | **Validate audio data** before feeding to models — reject corrupt data |
| 🔒 Security | **Sanitize LLM output** — the model can generate anything (HTML, script injections). Strip or escape. |
| 🔒 Security | **Sanitize transcription output** — Whisper can hallucinate URLs, emails, phone numbers |
| 🔒 Security | **Limit generation length** (`max_tokens=512`). Prevent endless generation. |
| 🔒 Security | **Never expose model internals** to the client (system prompts, model name, config) |
| 🔒 Security | **Prompt injection defense** — users could say "ignore your instructions..." Design robust system prompts. |
| ⚡ Performance | Load **all models at app startup**, not per-request. Use FastAPI `lifespan` events. |
| ⚡ Performance | Run STT in `asyncio.run_in_executor()` — it's CPU-bound. |
| ⚡ Performance | **Stream LLM tokens** — first token latency matters more than total generation time |
| ⚡ Performance | **Sentence-level TTS pipelining** — TTS sentence 1 while LLM generates sentence 2 |
| ⚡ Performance | Set `OMP_NUM_THREADS=6` for your Ryzen 5 5600 |
| ⚡ Performance | **Measure**: `stt_duration_ms`, `llm_time_to_first_token_ms`, `tokens_per_second`, `tts_duration_ms` |
| ⚡ Performance | Run TTS on CPU while LLM runs on GPU — **no resource contention** |
| 📈 Scalability | Provider pattern means you can flip to cloud APIs with one env var change |
| 📈 Scalability | **Concurrent session limit** — your 7800 XT handles 1-2 concurrent LLM sessions. Use a semaphore. |
| 🔧 Maintainability | **Externalize all model config** — model paths, temperature, max_tokens from env vars |
| 🔧 Maintainability | Write standalone test scripts for each provider |
| 🔧 Maintainability | Log model name, compute type, and device at startup |

### Checkpoint
> ✅ You should be able to: Speak → see transcription → see AI response stream → hear the AI speak back. Full voice conversation in < 3 seconds end-to-end on your local hardware. Toggle `AI_BACKEND=cloud` and it works the same way via cloud APIs. **This is the core product experience.**

---

## Phase 5 — Integration & Full Pipeline

> **Skill level:** Full-Stack Engineer  
> **Time estimate:** 3–5 days  
> **Goal:** Wire everything together into a seamless end-to-end experience

### What to Build

1. **End-to-End Pipeline**
   - User speaks → STT transcribes → transcript added to conversation → LLM generates → TTS speaks → user hears response
   - All flowing through the service interfaces from Phase 2
   - Stream LLM tokens to frontend AND to TTS simultaneously

2. **AI Scoring Feature** (LLM-based)
   - After interview ends, send full transcript to LLM with a scoring prompt
   - "Rate this candidate on: communication, technical depth, problem-solving..."
   - Store structured scores in PostgreSQL (Phase 3 schema)
   - Display scores on the dashboard

3. **Interview Configuration**
   - Let users choose: position type, difficulty level, focus areas
   - These configure the system prompt dynamically
   - Store config in the interview record

4. **Error Recovery**
   - WebSocket disconnects mid-interview → auto-save progress, allow reconnect
   - Model loading failure → health check reports unhealthy, don't accept sessions
   - Graceful degradation: if local model fails, fall back to cloud

5. **Polish the Frontend**
   - Real-time transcript display with proper formatting
   - Smooth audio playback
   - Loading states, error states, empty states
   - Interview summary view after completion

### Engineering Checklist — Phase 5

| Principle | Action |
|---|---|
| ⚡ Performance | **Measure end-to-end latency**: `user_stops_speaking → AI_audio_starts_playing`. Target < 3s. |
| ⚡ Performance | **Pre-warm all models** at startup — synthesize a test phrase, run a dummy inference |
| 📈 Scalability | Document your **scaling bottleneck map**: GPU (LLM) → CPU (STT) → CPU (TTS) |
| 🔧 Maintainability | Write an end-to-end integration test: send audio → receive transcript + AI response |
| 🔧 Maintainability | Add OpenTelemetry tracing: trace a request from WebSocket → STT → LLM → TTS → response |

### Checkpoint
> ✅ Full voice conversation with AI interviewer, plus interview scoring and dashboard. This is a **demoable product**.

---

## Phase 6 — Auth, Billing & Production Hardening 🔒💳

> **Skill level:** DevOps / Full-Stack  
> **Time estimate:** 7–10 days  
> **Goal:** Make it secure, billable, and production-ready

### What to Build

1. **Authentication & Authorization**
   - JWT-based auth (access + refresh tokens)
   - Protect REST endpoints with middleware
   - Protect WebSocket: validate token in handshake, reject unauthenticated connections
   - Angular auth guards for protected routes
   - Social login (Google OAuth) for frictionless signup

2. **Billing (Stripe Integration)**
   - Subscription plans: Free (3 interviews/month), Pro ($19/month), Premium ($49/month)
   - Stripe Checkout for payment
   - Webhook handler for subscription events (created, cancelled, failed)
   - Usage metering: count interviews per billing period
   - Angular billing/settings page

3. **API Security**
   - Rate limiting: per-user and per-IP (Redis token bucket)
   - Request size limits
   - Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP

4. **Docker Compose (Production)**
   - All services containerized with health checks
   - Separate Docker networks for isolation
   - Resource limits per container
   - SSL/TLS termination (nginx or Caddy reverse proxy)

5. **Monitoring & Observability**
   - Prometheus metrics:
     - `stt_inference_seconds`, `llm_tokens_per_second`, `llm_time_to_first_token_seconds`
     - `tts_synthesis_seconds`, `e2e_latency_seconds`
     - `active_sessions`, `websocket_connections_total`
   - Grafana dashboards
   - Structured logging (JSON) with correlation IDs per session
   - Error tracking (Sentry)

6. **Error Handling & Resilience**
   - VRAM exhaustion → graceful error, session recovery
   - Circuit breaker: if STT fails 5x → stop accepting audio for 30s
   - Auto-save interview on disconnect

### Engineering Checklist — Phase 6

| Principle | Action |
|---|---|
| 🔒 Security | **Penetration test** WebSocket endpoint — can unauthenticated clients connect? |
| 🔒 Security | **Dependency scanning** — `pip-audit` (Python), `npm audit` (Angular) in CI |
| 🔒 Security | **Secrets management** — Docker secrets or vault, not env vars in compose files |
| ⚡ Performance | **Load test** with realistic concurrent sessions. Know your limits. |
| ⚡ Performance | **Set up alerts** — e2e_latency > 5s for 5min, active_sessions > capacity |
| 📈 Scalability | Design LLM service call to be replaceable with HTTP call to remote LLM server |
| 🔧 Maintainability | **CI/CD pipeline** — lint, test, build Docker images on every push (GitHub Actions) |
| 🔧 Maintainability | **Health check endpoint** — `/health` returns status of all components |
| 🔧 Maintainability | **Runbook** — deploy, rollback, restart stuck session, upgrade model |

### Checkpoint
> ✅ Users can sign up, subscribe, and pay. The system is observable, secure, and resilient. **This is a launchable product.**

---

## Phase 7 — Advanced AI & Growth 🚀

> Once the core product works, these are the skills that separate a software engineer from an AI engineer:

### Topics to Explore

1. **Model Fine-Tuning**
   - Fine-tune Qwen2.5 on real interview transcripts to improve question quality
   - Tools: Unsloth, Axolotl, or QLoRA
   - This makes YOUR product unique — a fine-tuned model is your moat
   - Your 16GB RX 7800 XT may support fine-tuning with QLoRA (experiment)

2. **RAG (Retrieval Augmented Generation)**
   - Feed the LLM job descriptions, company values, role requirements
   - Use a vector database (ChromaDB, Milvus) to retrieve relevant context
   - The AI asks better questions when it knows the role

3. **Voice Cloning (Optional)**
   - Use XTTS v2 or Fish Speech to create custom interviewer voices
   - Different voices for different interview types

4. **Evaluation & Benchmarking**
   - How do you know if your AI interviewer is good?
   - Build eval datasets, measure response quality, track improvements
   - This is the hardest and most important AI engineering skill

5. **Multi-tenant Architecture**
   - Company A and Company B each get isolated data, prompts, and branding
   - Tenant-scoped database queries, per-tenant model configs
   - This is what makes it a real B2B SaaS product

6. **Mobile App / PWA**
   - Progressive Web App for mobile interview practice
   - Push notifications for interview reminders

---

## Hardware Profile — Your Hybrid Setup

```
┌─────────────────────────────────────────────────────┐
│  Ryzen 5 5600 (CPU)           RX 7800 XT (GPU)     │
│  6 cores / 12 threads         16GB VRAM, RDNA 3     │
│                                                      │
│  ┌───────────────────┐        ┌──────────────────┐  │
│  │ faster-whisper     │        │ llama.cpp        │  │
│  │ (STT, int8)       │        │ (Vulkan backend) │  │
│  │ ~500MB RAM         │        │ Qwen2.5-7B Q4    │  │
│  │ OMP_THREADS=6      │        │ ~4.5GB VRAM      │  │
│  └───────────────────┘        └──────────────────┘  │
│                                                      │
│  ┌───────────────────┐        Remaining VRAM:        │
│  │ Piper TTS          │        ~11.5GB (room for     │
│  │ ~100MB RAM         │        14B model or          │
│  │ ~50x real-time     │        concurrent sessions)  │
│  └───────────────────┘                               │
│                                                      │
│  Total RAM needed: ~8GB system + 4.5GB VRAM          │
└─────────────────────────────────────────────────────┘
```

### Performance Expectations

| Component | Speed | Status |
|---|---|---|
| Whisper `base` int8 (CPU) | 10s audio in ~2-3s | ✅ Real-time capable |
| Whisper `small` int8 (CPU) | 10s audio in ~5-6s | ✅ Usable with VAD |
| Qwen2.5-7B Q4_K_M (GPU Vulkan) | ~20-40 tok/s | 🚀 Excellent |
| Qwen2.5-14B Q4_K_M (GPU Vulkan) | ~10-20 tok/s | ✅ Good quality bump |
| Piper TTS (CPU) | ~50x real-time | ✅ Instant |
| **End-to-end latency** | **~2-3 seconds** | ✅ **Target met** |

> **Future GPU upgrade path:** If you get an NVIDIA GPU, the only changes are:
> 1. `device="cpu"` → `device="cuda"` in faster-whisper
> 2. Rebuild llama-cpp-python with `-DGGML_CUDA=on` instead of Vulkan
> 3. Everything else stays the same — your code architecture doesn't change

---

## Recommended Learning Order (Summary)

```
Phase 0: Project setup                    [1-2 days]   ← You know this
Phase 1: Frontend (Angular + Audio)       [5-7 days]   ← You know this + Angular + Web Audio
Phase 2: Backend (FastAPI + Interfaces)   [3-5 days]   ← You know this + pluggable design
Phase 3: Database & Storage               [3-5 days]   ← You know this
Phase 4: AI Models (STT + LLM + TTS)     [10-14 days]  ← 🧠🧠 CORE AI SKILLS
Phase 5: Integration & Pipeline           [3-5 days]   ← Wiring it all together
Phase 6: Auth, Billing & Production       [7-10 days]  ← You know this + Stripe
Phase 7: Advanced AI                      [Ongoing]    ← 🧠🧠🧠 GROWTH

Total estimated time: 6-8 weeks (part-time)
```

---

## Final Advice

1. **Don't optimize early.** Get the ugly version working first. Optimize latency after.
2. **Log everything.** Timestamps at each stage (audio received, STT done, LLM first token, TTS first chunk). This is how you find bottlenecks.
3. **Small models first.** Use Whisper `tiny`, Qwen2.5-3B while developing. Switch to larger models only when testing quality.
4. **Security is not Phase 6.** The checklists above embed security into every phase. Don't bolt it on at the end.
5. **Your AMD GPU is an advantage.** 16GB VRAM > 8GB NVIDIA in practice. Vulkan support in llama.cpp is mature.
6. **Build the interfaces first, models second.** The pluggable provider pattern from Phase 2 is your most important architectural decision.
7. **Read the source code.** When faster-whisper or llama-cpp-python does something unexpected, read their source. This builds deep understanding.
8. **Document your learnings.** Write notes in `docs/` after each phase. Future you will thank present you.
