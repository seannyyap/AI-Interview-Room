import numpy as np
from typing import Optional


class AudioBuffer:
    """
    Accumulates Float32 PCM audio chunks.
    Yields full buffers when a threshold is met.
    """
    def __init__(self, sample_rate: int = 16000, threshold_sec: float = 3.0, max_chunk_size: int = 1048576):
        self.sample_rate = sample_rate
        self.threshold_samples = int(sample_rate * threshold_sec)
        self.max_chunk_size = max_chunk_size
        self._buffer = np.array([], dtype=np.float32)

    def add_chunk(self, data: bytes) -> Optional[np.ndarray]:
        """
        Add a binary chunk (binary Float32).
        Returns full buffer if threshold is reached, else None.
        """
        if len(data) > self.max_chunk_size:
            raise ValueError(f"Chunk size {len(data)} exceeds limit {self.max_chunk_size}")

        chunk = np.frombuffer(data, dtype=np.float32)
        self._buffer = np.concatenate((self._buffer, chunk))

        if len(self._buffer) >= self.threshold_samples:
            full_buffer = self._buffer.copy()
            self._buffer = np.array([], dtype=np.float32)
            return full_buffer
        
        return None

    def clear(self):
        """Reset the buffer."""
        self._buffer = np.array([], dtype=np.float32)

    @property
    def current_duration(self) -> float:
        return len(self._buffer) / self.sample_rate
