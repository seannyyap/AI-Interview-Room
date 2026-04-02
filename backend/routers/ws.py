"""
WebSocket endpoint — real-time audio streaming and interview orchestration.

Phase 4: Wires STT → LLM → TTS pipeline using real providers from app.state.
"""
import asyncio
import numpy as np
import json
import logging
import re
import time
import random
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.database import AsyncSessionFactory
from backend.services.audio_buffer import AudioBuffer
from backend.services.session import SessionManager
from backend.services.conversation import ConversationManager
from backend.services.prompt_loader import build_interviewer_prompt
from backend.repositories.interview_repo import InterviewRepository
from backend.config import settings
from backend.models.schemas import (
    TranscriptMessage, AIResponseMessage, TTSAudioMessage,
    StatusMessage, ErrorMessage,
)

router = APIRouter()
logger = logging.getLogger("ws")

# Session manager (shared across connections)
session_manager = SessionManager()

# Regex to sanitise LLM output
_SCRIPT_TAG_RE = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize_llm_output(text: str) -> str:
    """Strip potential HTML/script injections from LLM output."""
    text = _SCRIPT_TAG_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    return text


def _is_sentence_end(text: str) -> bool:
    """Check if the accumulated text ends at a sentence or clause boundary."""
    # Period, question mark, exclamation, or a comma followed by space (for natural flow)
    return text.rstrip().endswith((".", "!", "?", ":", ";", ","))


async def _send_tts_audio(websocket: WebSocket, tts_provider, text: str) -> float:
    """Synthesize text and send TTS audio to the client. Returns synthesis time in ms."""
    if not text or not tts_provider.is_ready():
        return 0
    start = time.perf_counter()
    try:
        audio_bytes_out = await tts_provider.synthesize(text)
        synthesis_ms = (time.perf_counter() - start) * 1000
        if audio_bytes_out:
            duration_ms = int(
                len(audio_bytes_out) / 2  # 16-bit = 2 bytes/sample
                / settings.tts_sample_rate * 1000
            )
            await websocket.send_json(TTSAudioMessage(
                duration_ms=duration_ms,
                sample_rate=settings.tts_sample_rate,
            ).model_dump(by_alias=True))
            await websocket.send_bytes(audio_bytes_out)
            return synthesis_ms
    except Exception as e:
        logger.warning(f"TTS synthesis failed (non-fatal): {e}")
    return 0


@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and interview orchestration.

    Pipeline: Audio Chunks → STT → Conversation → LLM (streaming) → TTS → Audio Response
    """
    await websocket.accept()

    session_id = str(uuid4())
    user_id = "anonymous"
    client_ip = websocket.client.host if websocket.client else "unknown"
    await session_manager.create_session(session_id, user_id, client_ip)

    # Get providers from app.state (loaded during lifespan)
    stt_provider = websocket.app.state.stt_provider
    llm_provider = websocket.app.state.llm_provider
    tts_provider = websocket.app.state.tts_provider

    # Guard: check providers are ready before accepting work
    if not stt_provider.is_ready() or not llm_provider.is_ready():
        logger.error(f"Providers not ready — rejecting session {session_id}")
        await websocket.send_json(ErrorMessage(
            code="PROVIDERS_NOT_READY",
            message="AI models are still loading. Please try again in a moment."
        ).model_dump(by_alias=True))
        await websocket.close(code=1013, reason="Providers not ready")
        await session_manager.remove_session(session_id)
        return

    async with AsyncSessionFactory() as db:
        interview_repo = InterviewRepository(db)

        # Per-session services
        audio_buffer = AudioBuffer()
        conversation = ConversationManager()  # default prompt, updated on interview-start

        interview_id = None
        current_response_task = None  # Track the STT->LLM->TTS pipeline task for barge-in

        logger.info(f"New WebSocket session: {session_id} for user {user_id}")

        async def _run_response_pipeline(audio_data: np.ndarray):
            nonlocal current_response_task
            
            # 0. Setup TTS Worker Queue
            tts_queue = asyncio.Queue()
            
            # --- Human Pacing Delay ---
            # Simulate a 300ms–800ms "Listening/Planning" gap before starting processing
            listening_delay = random.uniform(0.3, 0.8)
            await asyncio.sleep(listening_delay)
            
            total_tts_ms = 0
            
            async def tts_worker():
                """Background task to synthesize and send audio concurrently."""
                nonlocal total_tts_ms
                while True:
                    sentence = await tts_queue.get()
                    if sentence is None:  # Sentinel to stop worker
                        tts_queue.task_done()
                        break
                    
                    try:
                        ms = await _send_tts_audio(websocket, tts_provider, sentence)
                        total_tts_ms += ms
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"[{session_id}] TTS worker error: {e}")
                    finally:
                        tts_queue.task_done()

            tts_task = asyncio.create_task(tts_worker())

            try:
                e2e_start = time.perf_counter()

                # 1. STT — transcribe audio
                stt_start = time.perf_counter()
                try:
                    transcript = await stt_provider.transcribe(audio_data, 16000)
                except Exception as e:
                    logger.error(f"[{session_id}] STT failed: {e}", exc_info=True)
                    await websocket.send_json(ErrorMessage(
                        code="STT_ERROR",
                        message="Speech recognition failed."
                    ).model_dump(by_alias=True))
                    return
                stt_ms = (time.perf_counter() - stt_start) * 1000

                if not transcript or not transcript.strip():
                    # Reset client status if we filtered out noise
                    await websocket.send_json(AIResponseMessage(
                        text="", is_complete=True
                    ).model_dump(by_alias=True))
                    return

                # Check if we were cancelled during STT
                await asyncio.sleep(0) 

                # 2. Persist user message
                await interview_repo.save_message(interview_id, "user", transcript)
                await db.commit()

                # 3. Send transcript to client
                await websocket.send_json(TranscriptMessage(
                    text=transcript,
                    is_final=True
                ).model_dump(by_alias=True))
                logger.info(f"[{session_id}] User: {transcript}")

                # 4. LLM — generate response (streaming)
                llm_start = time.perf_counter()
                llm_ttft_ms = 0
                
                conversation.add_user_message(transcript)
                full_ai_response = ""
                tts_sentence_buffer = ""

                try:
                    async for token in llm_provider.generate(conversation.get_history()):
                        if llm_ttft_ms == 0:
                            llm_ttft_ms = (time.perf_counter() - llm_start) * 1000
                            
                        clean_token = _sanitize_llm_output(token)
                        full_ai_response += clean_token
                        tts_sentence_buffer += clean_token

                        await websocket.send_json(AIResponseMessage(
                            text=clean_token,
                            is_complete=False
                        ).model_dump(by_alias=True))

                        if _is_sentence_end(tts_sentence_buffer):
                            sentence = tts_sentence_buffer.strip()
                            tts_sentence_buffer = ""
                            if sentence:
                                await tts_queue.put(sentence) # Non-blocking handoff to TTS worker

                except asyncio.CancelledError:
                    logger.info(f"LLM generation cancelled for session {session_id}")
                    raise
                except Exception as e:
                    logger.error(f"[{session_id}] LLM generation failed: {e}", exc_info=True)
                
                llm_total_ms = (time.perf_counter() - llm_start) * 1000

                # Remaining TTS/Finish
                if tts_sentence_buffer.strip():
                    await tts_queue.put(tts_sentence_buffer.strip())
                    
                # 5. Tell TTS worker we are done producing sentences and wait for it to finish sending audio
                await tts_queue.put(None)
                await tts_task 
                    
                if full_ai_response:
                    await interview_repo.save_message(interview_id, "ai", full_ai_response)
                    await db.commit()
                    logger.info(f"[{session_id}] AI: {full_ai_response}")
                    conversation.add_assistant_message(full_ai_response)

                total_e2e_ms = (time.perf_counter() - e2e_start) * 1000
                
                # Report accurate breakdown
                stats_msg = {
                    "type": "profiler-stats",
                    "stt_ms": round(stt_ms),
                    "llm_ttft_ms": round(llm_ttft_ms),
                    "llm_total_ms": round(llm_total_ms),
                    "tts_total_ms": round(total_tts_ms),
                    "total_e2e_ms": round(total_e2e_ms)
                }
                logger.info(f"[{session_id}] [Profiler] {stats_msg}")
                await websocket.send_json(stats_msg)

                await websocket.send_json(AIResponseMessage(
                    text="", is_complete=True
                ).model_dump(by_alias=True))
            except asyncio.CancelledError:
                logger.info(f"[Server Decision] Response pipeline CANCELLED (Barge-in detected) for session {session_id}")
                raise
            except Exception as e:
                logger.error(f"Response pipeline error: {e}", exc_info=True)
            finally:
                current_response_task = None
                
                # Cleanup: ensure TTS background worker shuts down if pipeline was cancelled early
                if not tts_task.done():
                    tts_task.cancel()

        try:
            await websocket.send_json(
                StatusMessage(status="ready").model_dump(by_alias=True)
            )

            while True:
                data = await websocket.receive()

                # --- Handle Binary Audio Chunks ---
                if "bytes" in data:
                    if not interview_id:
                        continue

                    audio_bytes = data["bytes"]
                    try:
                        audio_buffer.add_chunk(audio_bytes)
                    except ValueError as e:
                        logger.warning(f"Audio buffer error: {e}")
                        await websocket.send_json(ErrorMessage(
                            code="BUFFER_ERROR",
                            message=str(e)
                        ).model_dump(by_alias=True))

                # --- Handle Text JSON Commands ---
                elif "text" in data:
                    try:
                        command = json.loads(data["text"])
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON received: {e}")
                        await websocket.send_json(ErrorMessage(
                            code="INVALID_JSON",
                                message="Malformed JSON command"
                        ).model_dump(by_alias=True))
                        continue

                    cmd_type = command.get("type")

                    if cmd_type == "speech-end":
                        if not interview_id:
                            continue
                            
                        # Cancel any existing response if user starts a NEW thought
                        if current_response_task:
                            current_response_task.cancel()

                        full_buffer = audio_buffer.flush()
                        if full_buffer is not None:
                            current_response_task = asyncio.create_task(
                                _run_response_pipeline(full_buffer)
                            )

                    elif cmd_type == "speech-start":
                        # User started a new utterance — clear the "ghost buffer" of old static/echo
                        logger.info(f"[Server Decision] Speech-Start: Clearing ghost buffer for {session_id}")
                        audio_buffer.clear()

                    elif cmd_type == "interview-start":
                        config = command.get("config", {})
                        await session_manager.update_config(session_id, config)

                        # Build dynamic system prompt from interview config
                        system_prompt = build_interviewer_prompt(
                            position=config.get("position", "Software Engineer"),
                            difficulty=config.get("difficulty", "medium"),
                            focus_areas=config.get("focusAreas", config.get("focus_areas")),
                        )
                        conversation = ConversationManager(system_prompt=system_prompt)

                        # Create persistent Interview record
                        interview = await interview_repo.create_interview(
                            user_id=user_id,
                            position=config.get("position", "Software Engineer"),
                            config=config
                        )
                        await db.commit()
                        interview_id = interview.id

                        logger.info(f"Interview {interview_id} started for user {user_id}")
                        await websocket.send_json(
                            StatusMessage(status="interview_started").model_dump(by_alias=True)
                        )

                        # --- Initial Greeting ---
                        greeting_text = "Hello! I'm your AI interviewer today. Let's get started. Could you please introduce yourself and tell me a bit about your background?"
                        
                        # Send text response with is_complete=False to keep UI in PROCESSING
                        await websocket.send_json(AIResponseMessage(
                            text=greeting_text,
                            is_complete=False
                        ).model_dump(by_alias=True))
                        
                        # Persist and Speak
                        await interview_repo.save_message(interview_id, "ai", greeting_text)
                        await db.commit()
                        conversation.add_assistant_message(greeting_text)
                        await _send_tts_audio(websocket, tts_provider, greeting_text)
                        
                        # NOW send is_complete=True after audio has been streamed
                        await websocket.send_json(AIResponseMessage(
                            text="",
                            is_complete=True
                        ).model_dump(by_alias=True))

                    elif cmd_type == "interview-end":
                        if current_response_task:
                            current_response_task.cancel()
                        if interview_id:
                            await interview_repo.end_interview(interview_id)
                            await db.commit()
                            interview_id = None
                        break

        except WebSocketDisconnect:
            logger.info(f"WebSocket session disconnected: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error in {session_id}: {e}", exc_info=True)
            try:
                await websocket.send_json(ErrorMessage(
                    code="SERVER_ERROR",
                    message="Internal server error occurred"
                ).model_dump(by_alias=True))
            except Exception:
                pass
        finally:
            # 1. Cancel any background response task to prevent DB session leaks
            if current_response_task:
                current_response_task.cancel()
                
            # 2. Auto-end interview if client disconnects mid-session
            if interview_id:
                try:
                    await interview_repo.end_interview(interview_id)
                    await db.commit()
                    logger.info(f"Auto-ended interview {interview_id} on disconnect")
                except Exception as e:
                    logger.warning(f"Failed to auto-end interview: {e}")

            await session_manager.remove_session(session_id)
