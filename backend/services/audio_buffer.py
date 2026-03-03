"""
AudioBuffer — accumulates Float32 PCM audio chunks and yields
full buffers when a time threshold is reached.
"""
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("services.audio_buffer")


class AudioBuffer:
    """
    Accumulates Float32 PCM audio chunks.
    Yields full buffers when a threshold is met.
    """
    # Maximum total buffer size (60 seconds at 16kHz) to prevent memory exhaustion
    MAX_BUFFER_SAMPLES = 16000 * 60

    def __init__(self, sample_rate: int = 16000, threshold_sec: float = 1.5, max_chunk_size: int = 1048576):
        self.sample_rate = sample_rate
        self.threshold_samples = int(sample_rate * threshold_sec)
        self.silence_threshold = 0.01  # RMS threshold for silence
        self.silence_streak = 0        # Number of consecutive silent chunks
        self.REQUIRED_SILENCE_STREAK = 3 # ~750ms of silence (assuming 250ms chunks)
        self.max_chunk_size = max_chunk_size
        self._buffer = np.array([], dtype=np.float32)

    def add_chunk(self, data: bytes) -> None:
        """
        Add a binary chunk (binary Float32) to the internal buffer.
        No auto-flushing — server waits for explicit signal or limit.
        """
        if len(data) > self.max_chunk_size:
            raise ValueError(f"Chunk size {len(data)} exceeds limit {self.max_chunk_size}")

        if len(data) == 0:
            return

        # Validate that data length is a multiple of 4 (float32 = 4 bytes)
        if len(data) % 4 != 0:
            raise ValueError(
                f"Audio chunk size {len(data)} is not a multiple of 4 bytes (Float32)."
            )

        chunk = np.frombuffer(data, dtype=np.float32)

        # Check for NaN/Inf which indicate corrupted audio
        if not np.isfinite(chunk).all():
            logger.warning("Audio chunk contains NaN/Inf values — skipping")
            return

        self._buffer = np.concatenate((self._buffer, chunk))

        # Safety cap: prevent unbounded memory growth (e.g. 5 minutes)
        if len(self._buffer) > (self.sample_rate * 300):
            logger.warning("Audio buffer exceeded 5 minutes — truncating oldest samples")
            self._buffer = self._buffer[-(self.sample_rate * 60):]

    def flush(self) -> Optional[np.ndarray]:
        """
        Explicitly flush the current buffer.
        Returns the accumulated audio array, or None if empty.
        """
        if len(self._buffer) == 0:
            return None
            
        full_buffer = self._buffer.copy()
        self._buffer = np.array([], dtype=np.float32)
        self.silence_streak = 0
        return full_buffer

    def clear(self):
        """Reset the buffer."""
        self._buffer = np.array([], dtype=np.float32)

    @property
    def current_duration(self) -> float:
        return len(self._buffer) / self.sample_rate
