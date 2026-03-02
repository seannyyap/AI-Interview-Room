import json
import logging
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionFactory
from backend.services.audio_buffer import AudioBuffer
from backend.services.session import SessionManager
from backend.services.conversation import ConversationManager
from backend.repositories.interview_repo import InterviewRepository
from backend.providers.mock import MockSTTProvider, MockLLMProvider
from backend.models.schemas import TranscriptMessage, AIResponseMessage, StatusMessage, ErrorMessage

router = APIRouter()
logger = logging.getLogger("ws")

# Globals for Session/Provider Management
session_manager = SessionManager()
stt_provider = MockSTTProvider()  # To be replaced with faster-whisper in Phase 4
llm_provider = MockLLMProvider()  # To be replaced with local LLM in Phase 4

@router.websocket("/ws/audio")
async def websocket_endpoint(
    websocket: WebSocket
):
    """
    WebSocket endpoint for real-time audio streaming and interview orchestration.
    """
    await websocket.accept()
    
    session_id = str(uuid4())
    user_id = "anonymous"  # Default user for unauthenticated sessions
    client_ip = websocket.client.host
    await session_manager.create_session(session_id, user_id, client_ip)
    
    # DB session for persistence
    async with AsyncSessionFactory() as db:
        interview_repo = InterviewRepository(db)
        
        # Per-session services
        audio_buffer = AudioBuffer()
        conversation = ConversationManager()
        
        # We delay Interview record creation until 'interview-start' command
        interview_id = None
        
        logger.info(f"New WebSocket session: {session_id} for user {user_id}")
        
        try:
            # Send initial status
            await websocket.send_json(StatusMessage(status="ready").model_dump(by_alias=True))
            
            while True:
                data = await websocket.receive()
                
                # --- Handle Binary Audio Chunks ---
                if "bytes" in data:
                    if not interview_id:
                        # Don't process audio if interview hasn't started
                        continue
                        
                    audio_bytes = data["bytes"]
                    try:
                        full_buffer = audio_buffer.add_chunk(audio_bytes)
                        
                        if full_buffer is not None:
                            # 1. Process STT
                            transcript = await stt_provider.transcribe(full_buffer, 16000)
                            
                            # 2. Persist user message to DB
                            await interview_repo.save_message(interview_id, "user", transcript)
                            await db.commit()
                            
                            # 3. Send transcript to client
                            await websocket.send_json(TranscriptMessage(
                                text=transcript,
                                is_final=True
                            ).model_dump(by_alias=True))
                            
                            # 4. Process LLM
                            conversation.add_user_message(transcript)
                            full_ai_response = ""
                            
                            async for token in llm_provider.generate(conversation.get_history()):
                                full_ai_response += token
                                await websocket.send_json(AIResponseMessage(
                                    text=token,
                                    is_complete=False
                                ).model_dump(by_alias=True))
                            
                            # 5. Persist AI response message to DB
                            await interview_repo.save_message(interview_id, "ai", full_ai_response)
                            await db.commit()
                            
                            # Finalize response
                            conversation.add_assistant_message(full_ai_response)
                            await websocket.send_json(AIResponseMessage(
                                text="",
                                is_complete=True
                            ).model_dump(by_alias=True))
                            
                    except ValueError as e:
                        logger.warning(f"Audio buffer error: {e}")
                        await websocket.send_json(ErrorMessage(
                            code="BUFFER_ERROR",
                            message=str(e)
                        ).model_dump(by_alias=True))

                # --- Handle Text JSON Commands ---
                elif "text" in data:
                    command = json.loads(data["text"])
                    if command.get("type") == "interview-start":
                        config = command.get("config")
                        await session_manager.update_config(session_id, config)
                        
                        # Create persistent Interview record
                        interview = await interview_repo.create_interview(
                            user_id=user_id,
                            position=config.get("position", "Software Engineer"),
                            config=config
                        )
                        await db.commit()
                        interview_id = interview.id
                        
                        logger.info(f"Interview {interview_id} started for user {user_id}")
                        await websocket.send_json(StatusMessage(status="interview_started").model_dump(by_alias=True))
                        
                    elif command.get("type") == "interview-end":
                        if interview_id:
                            await interview_repo.end_interview(interview_id)
                            await db.commit()
                        break
                        
        except WebSocketDisconnect:
            logger.info(f"WebSocket session disconnected: {session_id}")
            if interview_id:
                # We don't necessarily end the interview on disconnect to allow resumption
                # but for now we'll just log it.
                pass
        except Exception as e:
            logger.error(f"WebSocket error in {session_id}: {e}", exc_info=True)
            try:
                await websocket.send_json(ErrorMessage(
                    code="SERVER_ERROR",
                    message="Internal server error occurred"
                ).model_dump(by_alias=True))
            except:
                pass
        finally:
            await session_manager.remove_session(session_id)
