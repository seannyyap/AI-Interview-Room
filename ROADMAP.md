# AI Interview Room — Technical Documentation & Roadmap

This document serves as the primary technical reference for the AI Interview Room. It outlines the architecture, the AI pipeline, and the research-backed humanization logic that drives the conversational experience.

---

## 🏗️ System Architecture

The AI Interview Room is a **Hybrid-Cloud** application designed for low-latency, natural voice interaction.

- **Frontend**: Angular 17+ with Signals and RxJS. Handles real-time audio capture, VAD, and playback.
- **Backend**: FastAPI (Python) orchestrator. Manages WebSocket sessions, conversation history, and coordinates the AI providers.
- **Database**: PostgreSQL (SQLAlchemy/Alembic) for interview transcripts and persistence.

### High-Level Data Flow
1. **Audio Capture**: Browser captures mic at 48kHz, downsamples to 16kHz via `AudioWorklet`.
2. **Client-Side VAD**: `AnalyserNode` monitors energy in the human voice band (300Hz-3000Hz).
3. **WebSocket Streaming**: 16kHz Mono Float32 PCM chunks are streamed via WebSocket.
4. **AI Pipeline**: STT (Whisper) → LLM (Groq Llama 3) → TTS (Kokoro).
5. **Playback**: 24kHz PCM returned to browser and queued for gapless playback.

---

## 🧠 AI Pipeline: The "Brain"

### 1. Speech-To-Text (STT)
- **Local Provider**: Powered by `faster-whisper`.
- **Model**: `distil-small.en` or `base` running on CPU (Fast and efficient).
- **Optimization**: Uses `int8` quantization to ensure sub-second transcription on standard CPUs.

### 2. Large Language Model (LLM)
- **Primary Provider**: **Groq API**.
- **Model**: `llama-3.1-8b-instant`.
- **Latency**: Groq's LPU architecture provides 800+ tokens/sec, enabling near-instant response generation.
- **Hybrid Strategy**: Backend configuration allows swapping to `local-cpp` (Llama.cpp via Vulkan) for full privacy.

### 3. Text-To-Speech (TTS)
- **Local Provider**: `Kokoro TTS`.
- **Optimization**: Sentence-level streaming. The LLM produces a sentence, and the TTS immediately starts synthesizing while the LLM continues generating the rest of the text.
- **Performance**: High-quality natural voice running efficiently on CPU.

---

## 🎭 Humanization & Turn-Taking

Based on linguistic research, the system models natural human conversational cues.

### 1. Turn-Taking Engine
- **Half-Duplex Logic**: To prevent echo loops and ensure clear boundaries, the microphone is suppressed while the AI is thinking or speaking.
- **Thinking Room (2.0s Pause)**: The VAD waits for 2 seconds of silence before committing a "Speech End." This allows the candidate to pause and reflect without being interrupted.
- **Natural Response Delay**: A random **300ms–800ms** delay is added before the AI starts speaking to simulate human cognitive load (listening/planning).

### 2. Personality & Disfluencies
The AI is prompted to behave like a human interviewer, not a machine:
- **Fillers**: Uses disfluencies like "Hmm…", "Uh…", or "So…" to signal thinking.
- **Adjacency Pairs**: Always acknowledges the user's last statement ("I see your point," "Interesting approach") before moving to the next question.
- **Backchanneling**: Provides social cues and emotional reactions where appropriate.

---

## 📊 Latency Profiling

Every response trip is measured and logged to the browser console:
- **STT**: Transcription time.
- **TTFT (Time To First Token)**: Speed of the LLM.
- **TTS Total**: Total synthesis time for the response.
- **End-to-End**: The total perceived latency from "User Stop" to "AI Audio Start."

---

## 🛠️ Performance & Scalability (Hardware Profile)

The stack is optimized for the following hybrid setup:
- **CPU (Ryzen 5 5600)**: Handles STT and TTS (Local).
- **Network**: Groq handles the heavy LLM lifting.
- **Browser**: Handles VAD and Downsampling to reduce server load.

---

## 🚀 Roadmap: What's Next?

### Phase 5: Production Hardening (Current Focus)
- [ ] **Google OAuth**: Frictionless sign-on.
- [ ] **Stripe Integration**: Subscription tiers and usage metering.
- [ ] **Advanced Analytics**: Detailed feedback report after each session.

### Phase 6: Growth & Specialized AI
- [ ] **RAG Support**: Upload job descriptions to tailor the interview.
- [ ] **Fine-Tuning**: Train a local Qwen model on 10,000+ real interview transcripts.
- [ ] **Multi-Voice Support**: Choose between different interviewer personas.
