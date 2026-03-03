"""
Unit tests for Pydantic schemas — serialization, camelCase aliases, defaults.
"""
from backend.models.schemas import (
    StatusMessage, ErrorMessage, TranscriptMessage,
    AIResponseMessage, TTSAudioMessage, HealthStatus
)


class TestStatusMessage:
    def test_type_default(self):
        msg = StatusMessage(status="ready")
        assert msg.type == "status"

    def test_serialization(self):
        msg = StatusMessage(status="ready")
        d = msg.model_dump(by_alias=True)
        assert d["type"] == "status"
        assert d["status"] == "ready"


class TestErrorMessage:
    def test_fields(self):
        msg = ErrorMessage(code="TEST_ERR", message="Something broke")
        assert msg.type == "error"
        assert msg.code == "TEST_ERR"
        assert msg.message == "Something broke"


class TestTranscriptMessage:
    def test_camel_case_alias(self):
        msg = TranscriptMessage(text="hello", is_final=True)
        d = msg.model_dump(by_alias=True)
        assert "isFinal" in d
        assert d["isFinal"] is True

    def test_has_timestamp(self):
        msg = TranscriptMessage(text="test", is_final=False)
        assert msg.timestamp  # should auto-generate


class TestAIResponseMessage:
    def test_camel_case_alias(self):
        msg = AIResponseMessage(text="token", is_complete=False)
        d = msg.model_dump(by_alias=True)
        assert "isComplete" in d
        assert d["isComplete"] is False


class TestTTSAudioMessage:
    def test_defaults(self):
        msg = TTSAudioMessage(duration_ms=500)
        d = msg.model_dump(by_alias=True)
        assert d["sampleRate"] == 24000
        assert d["channels"] == 1
        assert d["bitDepth"] == 16
        assert d["durationMs"] == 500


class TestHealthStatus:
    def test_fields(self):
        msg = HealthStatus(
            status="ok", version="0.4.0",
            ai_backend="local",
            stt_ready=True, llm_ready=False, tts_ready=True
        )
        d = msg.model_dump(by_alias=True)
        assert d["status"] == "ok"
        assert d["aiBackend"] == "local"
        assert d["sttReady"] is True
        assert d["llmReady"] is False
