---
name: ai-interview-pipeline
description: Orchestrates the real-time interview pipeline—WebSocket audio streaming, STT (faster-whisper/cloud), LLM (Groq/local-cpp), sentence-level TTS (Kokoro). Use when modifying the pipeline, adding providers, or debugging latency, VAD, or turn-taking.
---

# AI Interview Pipeline

## Data Flow

1. **Audio capture** (frontend): 48kHz mic → downsample to 16kHz mono Float32 via AudioWorklet → stream chunks over WebSocket.
2. **Client VAD**: `speech-start` clears buffer; 2s silence → `speech-end` commits buffer and triggers pipeline.
3. **Backend pipeline** (`backend/routers/ws.py`): Audio → STT → persist user message → LLM (streaming) → sentence-level TTS → send text + binary audio to client.
4. **Playback** (frontend): TTS metadata (`tts-audio`) then raw PCM; queue for gapless playback at configured sample rate.

## WebSocket Contract

### Client → Server

| type | When | Payload |
|------|------|---------|
| (binary) | While speaking | Float32 PCM, 16kHz mono (ArrayBuffer) |
| `speech-start` | User starts talking | Clears "ghost" buffer server-side |
| `speech-end` | 2s silence after speech | Triggers STT → LLM → TTS pipeline |
| `interview-start` | Start session | `{ config: { position, difficulty, focusAreas } }` |
| `interview-end` | End session | — |

### Server → Client

| type | Meaning |
|------|---------|
| `status` | `ready` \| `interview_started` |
| `transcript` | User transcript; `isFinal: true` when committed |
| `ai-response` | Streaming tokens; `isComplete: true` when turn done |
| `tts-audio` | Metadata (sampleRate, durationMs, etc.); next message is **binary** PCM |
| `error` | `{ code, message }` — see Error codes |
| `profiler-stats` | `stt_ms`, `llm_ttft_ms`, `llm_total_ms`, `tts_total_ms`, `total_e2e_ms` |

### Error codes

- `PROVIDERS_NOT_READY` — models still loading; close 1013.
- `STT_ERROR` — speech recognition failed.
- `BUFFER_ERROR` — audio buffer validation failed.
- `INVALID_JSON` — malformed JSON command.
- `SERVER_ERROR` — generic server failure.

## Humanization & Turn-Taking

- **Thinking room**: VAD waits 2s silence before `speech-end` (no early cut-off).
- **Response delay**: 300–800ms random delay before starting STT (simulated listening/planning).
- **Barge-in**: On new `speech-end`, cancel any running `current_response_task` (and TTS worker) so the new utterance wins.

## Key Files

- Backend: `backend/routers/ws.py`, `backend/services/audio_buffer.py`, `backend/providers/*`.
- Frontend: `frontend/src/app/shared/services/websocket.service.ts`, `audio-capture.service.ts`, `audio-playback.service.ts`, `shared/models/websocket.models.ts`.
- Schemas: `backend/models/schemas.py` (Pydantic; camelCase via `to_camel`, `model_dump(by_alias=True)`).

## Adding a Provider

1. Implement the provider interface (e.g. `transcribe(audio, sample_rate)`, `generate(history)`, `synthesize(text)`).
2. Load in `main.py` lifespan; set `app.state.stt_provider` / `llm_provider` / `tts_provider`.
3. Guards: call `provider.is_ready()` before accepting work; return `PROVIDERS_NOT_READY` if not ready.
