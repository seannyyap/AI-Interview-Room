"""
Cloud STT Provider — Deepgram REST API.

Implements STTProvider protocol. Sends audio to Deepgram's
speech-to-text endpoint and returns the transcript.
"""
import io
import logging
import time
import wave

import httpx
import numpy as np

from backend.config import settings

logger = logging.getLogger("providers.cloud_stt")


def _audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Convert a float32 numpy array to WAV bytes (16-bit PCM)."""
    int16_audio = (audio * 32767).clip(-32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int16_audio.tobytes())
    return buf.getvalue()


class CloudSTTProvider:
    """
    Speech-to-Text via Deepgram REST API.

    Requires DEEPGRAM_API_KEY in environment / settings.
    """

    DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"

    def __init__(self) -> None:
        self._api_key: str | None = settings.deepgram_api_key
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        if not self._api_key:
            raise ValueError("DEEPGRAM_API_KEY is not set — cannot use cloud STT")
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info("Cloud STT provider ready (Deepgram)")

    def is_ready(self) -> bool:
        return self._client is not None and bool(self._api_key)

    async def unload(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Cloud STT provider closed")

    # ── Inference ────────────────────────────────────────────

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Send audio to Deepgram and return the transcript."""
        if self._client is None:
            raise RuntimeError("Cloud STT not loaded — call load() first")

        wav_bytes = _audio_to_wav_bytes(audio, sample_rate)

        start = time.perf_counter()
        response = await self._client.post(
            self.DEEPGRAM_URL,
            headers={
                "Authorization": f"Token {self._api_key}",
                "Content-Type": "audio/wav",
            },
            params={
                "model": "nova-2",
                "language": "en",
                "smart_format": "true",
            },
            content=wav_bytes,
        )
        response.raise_for_status()

        elapsed_ms = (time.perf_counter() - start) * 1000
        result = response.json()
        transcript = (
            result.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("transcript", "")
        )

        # logger.info(f"Cloud STT transcribed in {elapsed_ms:.0f}ms: '{transcript[:80]}...'")
        return transcript.strip()
