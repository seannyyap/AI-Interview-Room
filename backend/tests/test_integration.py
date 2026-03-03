"""
Integration tests — API endpoints and WebSocket pipeline with mock providers.

Uses the test app from conftest.py which provides:
- Mock STT/LLM/TTS providers
- In-memory SQLite database
"""
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_all_providers_ready(self, client: TestClient):
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["sttReady"] is True
        assert data["llmReady"] is True
        assert data["ttsReady"] is True

    def test_health_has_version(self, client: TestClient):
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data


class TestInterviewsEndpoint:
    def test_list_interviews_empty(self, client: TestClient):
        response = client.get("/api/interviews")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestWebSocketConnection:
    def test_connect_receives_ready(self, client: TestClient):
        """Client should receive a 'status: ready' message on connect."""
        with client.websocket_connect("/ws/audio") as ws:
            data = ws.receive_json()
            assert data["type"] == "status"
            assert data["status"] == "ready"

    def test_audio_without_interview_ignored(self, client: TestClient):
        """Audio sent without starting an interview should be silently ignored."""
        with client.websocket_connect("/ws/audio") as ws:
            ws.receive_json()  # status: ready
            # Send audio without starting interview
            audio = np.zeros(48000, dtype=np.float32)
            ws.send_bytes(audio.tobytes())
            # Should not crash or return anything (no interview_id set)
            # Send interview-end to cleanly close
            ws.send_json({"type": "interview-end"})

    def test_full_pipeline(self, client: TestClient):
        """Full flow: connect → start interview → send audio → receive transcript + AI response."""
        with client.websocket_connect("/ws/audio") as ws:
            # 1. Receive ready
            data = ws.receive_json()
            assert data["status"] == "ready"

            # 2. Start interview
            ws.send_json({
                "type": "interview-start",
                "config": {
                    "position": "Software Engineer",
                    "difficulty": "medium",
                    "focusAreas": ["system design"]
                }
            })
            status = ws.receive_json()
            assert status["type"] == "status"
            assert status["status"] == "interview_started"

            # 3. Send 3 seconds of audio (threshold)
            audio = np.zeros(48000, dtype=np.float32)
            ws.send_bytes(audio.tobytes())

            # 4. Receive transcript
            transcript = ws.receive_json()
            assert transcript["type"] == "transcript"
            assert transcript["isFinal"] is True
            assert len(transcript["text"]) > 0

            # 5. Receive streaming AI response tokens
            tokens_received = 0
            completion_received = False
            while True:
                msg = ws.receive_json()
                if msg["type"] == "ai-response":
                    tokens_received += 1
                    if msg["isComplete"]:
                        completion_received = True
                        break

            assert tokens_received > 1  # Should receive multiple tokens
            assert completion_received is True

            # 6. End interview
            ws.send_json({"type": "interview-end"})

    def test_large_chunk_rejected(self, client: TestClient):
        """Audio chunks > 1MB should be rejected with error."""
        with client.websocket_connect("/ws/audio") as ws:
            ws.receive_json()  # status: ready

            # Start interview first
            ws.send_json({
                "type": "interview-start",
                "config": {
                    "position": "Test",
                    "difficulty": "easy",
                    "focusAreas": []
                }
            })
            ws.receive_json()  # interview_started

            # Send 2MB chunk
            large = np.zeros(524288, dtype=np.float32)  # 2MB
            ws.send_bytes(large.tobytes())

            resp = ws.receive_json()
            assert resp["type"] == "error"
            assert resp["code"] == "BUFFER_ERROR"

    def test_invalid_json_handled(self, client: TestClient):
        """Malformed JSON should return an error, not crash."""
        with client.websocket_connect("/ws/audio") as ws:
            ws.receive_json()  # status: ready
            ws.send_text("not valid json {{{")
            resp = ws.receive_json()
            assert resp["type"] == "error"
            assert resp["code"] == "INVALID_JSON"

    def test_interview_creates_db_record(self, client: TestClient):
        """Starting an interview should create a DB record visible via API."""
        with client.websocket_connect("/ws/audio") as ws:
            ws.receive_json()  # ready
            ws.send_json({
                "type": "interview-start",
                "config": {
                    "position": "Data Scientist",
                    "difficulty": "hard",
                    "focusAreas": ["ML"]
                }
            })
            ws.receive_json()  # started
            ws.send_json({"type": "interview-end"})

        # Check interview exists in DB
        response = client.get("/api/interviews")
        interviews = response.json()
        assert any(iv["position"] == "Data Scientist" for iv in interviews)
