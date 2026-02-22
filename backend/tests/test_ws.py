import pytest
import numpy as np
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify the health check endpoint works."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_list_interviews():
    """Verify the mock interviews endpoint."""
    response = client.get("/api/interviews")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_websocket_connection():
    """
    Verify the WebSocket audio pipeline.
    Test: Connect -> Receive 'ready' -> Send audio -> Receive Transcript & AI Response
    """
    with client.websocket_connect("/ws/audio") as websocket:
        # 1. Receive initial status
        data = websocket.receive_json()
        assert data["type"] == "status"
        assert data["status"] == "ready"

        # 2. Send 3 seconds of dummy audio (Float32 PCM at 16kHz)
        # 3 seconds * 16000 samples = 48000 samples
        audio_data = np.zeros(48000, dtype=np.float32)
        websocket.send_bytes(audio_data.tobytes())

        # 3. Receive Transcript
        transcript_data = websocket.receive_json()
        assert transcript_data["type"] == "transcript"
        assert "Mock transcript" in transcript_data["text"]

        # 4. Receive streaming AI Response tokens
        # The mock provider sends multiple words
        first_token = websocket.receive_json()
        assert first_token["type"] == "ai-response"
        assert first_token["isComplete"] is False

        # Drain tokens until completion
        is_complete = False
        while not is_complete:
            resp = websocket.receive_json()
            if resp["type"] == "ai-response" and resp["isComplete"]:
                is_complete = True
        
        assert is_complete is True

def test_websocket_large_chunk_rejection():
    """Verify security check: reject chunks > 1MB."""
    with client.websocket_connect("/ws/audio") as websocket:
        websocket.receive_json() # status: ready
        
        # 2MB of zeros
        large_data = np.zeros(524288, dtype=np.float32) # 524288 * 4 bytes = 2MB
        websocket.send_bytes(large_data.tobytes())
        
        resp = websocket.receive_json()
        assert resp["type"] == "error"
        assert resp["code"] == "BUFFER_ERROR"
