---
name: roadmap-phase5-phase6
description: Implements roadmap items—Google OAuth, Stripe subscriptions, post-session analytics, RAG from job descriptions, fine-tuning on interview transcripts, multi-voice TTS. Use when scoping or implementing these features.
---

# Roadmap: Phase 5 & Phase 6

## Phase 5 — Production Hardening

### Google OAuth

- Frictionless sign-on; no storing passwords. Use OIDC/OAuth2 (e.g. Google Identity, or Auth0/Okta with Google).
- Backend: validate token or exchange code for session; set `user_id` on session/interview (replace anonymous).
- Frontend: redirect to provider, handle callback, send auth token (e.g. Bearer) or cookie with API/WS requests.

### Stripe Integration

- Subscription tiers and usage metering. Use Stripe Products/Prices, Customers, Subscriptions; meter by interview count or minutes if needed.
- Webhooks: handle `customer.subscription.*`, `invoice.*`; keep local state in sync (e.g. `user.subscription_status`).
- Prefer Stripe MCP or official Stripe docs when implementing; store keys in env.

### Advanced Analytics

- Detailed feedback report after each session: persist scores, topics covered, suggested improvements. Add API endpoint(s) to fetch report by `interview_id`; consider storing structured feedback in DB (e.g. JSON or dedicated tables).

## Phase 6 — Growth & Specialized AI

### RAG Support

- Upload job descriptions; use as context for the interviewer prompt. Ingest into vector store or append to system prompt; retrieve relevant chunks when building `build_interviewer_prompt` or per-turn context.

### Fine-Tuning

- Train a local model (e.g. Qwen) on 10k+ real interview transcripts. Export transcripts from `Interview` + messages; format as instruction/response pairs; use existing fine-tuning tooling (e.g. Ollama, or cloud fine-tune). Keep inference path compatible with current LLM provider interface.

### Multi-Voice Support

- Allow choosing interviewer persona/voice. Backend: add `tts_voice` (or persona id) to interview config; TTS provider selects voice. Frontend: add voice/persona selector in interview config UI; send in `interview-start.config`.

## Cross-Cutting

- All new features: respect existing config (env), logging, and error handling patterns. Use backend repositories for new persistence; keep WebSocket contract backward-compatible where possible.
