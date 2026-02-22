import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.audio_buffer import AudioBuffer
from backend.services.session import SessionManager
from backend.services.conversation import ConversationManager
from backend.providers.mock import MockSTTProvider, MockLLMProvider
from backend.models.schemas import TranscriptMessage, AIResponseMessage, StatusMessage, ErrorMessage

router = APIRouter()
logger = logging.getLogger("ws")

# Globals for Phase 2 (will be dependency-injected in later phases)
session_manager = SessionManager()
stt_provider = MockSTTProvider()
llm_provider = MockLLMProvider()

@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    client_ip = websocket.client.host
    session = session_manager.create_session(client_ip)
    
    # Per-session services
    audio_buffer = AudioBuffer()
    conversation = ConversationManager()
    
    logger.info(f"New WebSocket session: {session.id} from {client_ip}")
    
    try:
        # 1. Send initial status
        await websocket.send_json(StatusMessage(status="ready").model_dump(by_alias=True))
        
        while True:
            data = await websocket.receive()
            
            # --- Handle Binary Audio Chunks ---
            if "bytes" in data:
                audio_bytes = data["bytes"]
                try:
                    full_buffer = audio_buffer.add_chunk(audio_bytes)
                    
                    if full_buffer is not None:
                        # Process audio (Mock STT)
                        transcript = await stt_provider.transcribe(full_buffer, 16000)
                        
                        # Send interim transcript
                        await websocket.send_json(TranscriptMessage(
                            text=transcript,
                            is_final=True
                        ).model_dump(by_alias=True))
                        
                        # Process LLM (Mock LLM)
                        conversation.add_user_message(transcript)
                        full_ai_response = ""
                        
                        async for token in llm_provider.generate(conversation.get_history()):
                            full_ai_response += token
                            await websocket.send_json(AIResponseMessage(
                                text=token,
                                is_complete=False
                            ).model_dump(by_alias=True))
                        
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
                    session_manager.update_config(session.id, command.get("config"))
                    logger.info(f"Session {session.id} started with config: {command.get('config')}")
                elif command.get("type") == "interview-end":
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket session disconnected: {session.id}")
    except Exception as e:
        logger.error(f"WebSocket error in {session.id}: {e}", exc_info=True)
        try:
            await websocket.send_json(ErrorMessage(
                code="SERVER_ERROR",
                message="Internal server error occurred"
            ).model_dump(by_alias=True))
        except:
            pass
    finally:
        session_manager.remove_session(session.id)
