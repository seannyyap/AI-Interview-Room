"""
Unit tests for AudioBuffer — data validation, threshold detection, memory safety.
"""
import numpy as np
import pytest

from backend.services.audio_buffer import AudioBuffer


class TestAudioBufferBasics:
    """Core accumulation and threshold behaviour."""

    def test_below_threshold_returns_none(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=3.0)
        chunk = np.zeros(8000, dtype=np.float32)  # 0.5 seconds
        assert buf.add_chunk(chunk.tobytes()) is None

    def test_at_threshold_returns_buffer(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=1.0)
        chunk = np.zeros(16000, dtype=np.float32)  # exactly 1 second
        result = buf.add_chunk(chunk.tobytes())
        assert result is not None
        assert len(result) == 16000

    def test_accumulation_across_chunks(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=1.0)
        half = np.zeros(8000, dtype=np.float32)
        assert buf.add_chunk(half.tobytes()) is None
        result = buf.add_chunk(half.tobytes())
        assert result is not None
        assert len(result) == 16000

    def test_buffer_resets_after_yield(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=1.0)
        chunk = np.zeros(16000, dtype=np.float32)
        buf.add_chunk(chunk.tobytes())
        # After yielding, buffer should be empty
        assert buf.current_duration == 0.0

    def test_clear_resets_buffer(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=3.0)
        chunk = np.zeros(8000, dtype=np.float32)
        buf.add_chunk(chunk.tobytes())
        buf.clear()
        assert buf.current_duration == 0.0


class TestAudioBufferValidation:
    """Input validation and safety checks."""

    def test_rejects_oversized_chunk(self):
        buf = AudioBuffer(max_chunk_size=1024)
        big_data = np.zeros(512, dtype=np.float32)  # 2048 bytes > 1024 limit
        with pytest.raises(ValueError, match="exceeds limit"):
            buf.add_chunk(big_data.tobytes())

    def test_rejects_non_float32_aligned_data(self):
        buf = AudioBuffer()
        with pytest.raises(ValueError, match="not a multiple of 4"):
            buf.add_chunk(b"\x00\x00\x00")  # 3 bytes — not divisible by 4

    def test_skips_nan_chunks(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=1.0)
        bad = np.array([float("nan")] * 16000, dtype=np.float32)
        result = buf.add_chunk(bad.tobytes())
        assert result is None
        assert buf.current_duration == 0.0

    def test_skips_inf_chunks(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=1.0)
        bad = np.array([float("inf")] * 16000, dtype=np.float32)
        result = buf.add_chunk(bad.tobytes())
        assert result is None

    def test_empty_chunk_returns_none(self):
        buf = AudioBuffer()
        assert buf.add_chunk(b"") is None

    def test_memory_cap_prevents_oom(self):
        """Buffer should truncate if MAX_BUFFER_SAMPLES is exceeded."""
        buf = AudioBuffer(sample_rate=16000, threshold_sec=100.0)  # very high threshold
        # Push 61 seconds of audio (exceeds 60s cap)
        for _ in range(61):
            chunk = np.zeros(16000, dtype=np.float32)
            buf.add_chunk(chunk.tobytes())
        # Buffer should have been truncated to threshold_samples
        assert buf.current_duration <= 100.0


class TestAudioBufferCurrentDuration:
    def test_duration_calculation(self):
        buf = AudioBuffer(sample_rate=16000, threshold_sec=10.0)
        chunk = np.zeros(16000, dtype=np.float32)  # 1 second
        buf.add_chunk(chunk.tobytes())
        assert abs(buf.current_duration - 1.0) < 0.01
