---
name: frontend-angular-signals
description: Angular 17+ with Signals and RxJS. Use when changing interview UI, WebSocket handling, or audio capture/playback services.
---

# Frontend Angular Conventions

## State & Reactivity

- Prefer **Signals** for component state: `signal()`, `computed()`, `asReadonly()`.
- Use **RxJS** for streams: WebSocket messages, audio, timers. Expose as `Observable` (e.g. `transcript$`, `aiResponse$`) and subscribe in components or effects.

## WebSocket & Audio

- **WebSocketService**: Connects to `/ws/audio` (or `environment.wsUrl`). Sends binary chunks and JSON commands; receives JSON + binary TTS. Message types must match `frontend/src/app/shared/models/websocket.models.ts`.
- **AudioCaptureService**: Mic capture, downsampling to 16kHz; emits chunks and VAD events (`speech-start`, `speech-end` with 2s thinking room).
- **AudioPlaybackService**: Queues PCM buffers; plays after `tts-audio` metadata; gapless playback at configured sample rate.

## Dependency Injection

- Inject services via `inject(Service)` in constructors or field initializers.
- Services used across the app: `providedIn: 'root'`.

## Style

- Match project Prettier: single quotes, `printWidth: 100` (see `frontend/package.json`).
- Keep component templates and styles colocated; use Angular Material where applicable (`@angular/material`, `@angular/cdk`).

## Message Contract

- Outgoing: `interview-start` (with `config.position`, `config.difficulty`, `config.focusAreas`), `interview-end`, binary audio.
- Incoming: `status`, `transcript`, `ai-response`, `tts-audio` (+ binary), `error`, `profiler-stats`. Use the same type names and camelCase as in `websocket.models.ts`.
