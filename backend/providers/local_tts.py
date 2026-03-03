"""
Local TTS Provider — Kokoro TTS on CPU.

Implements TTSProvider protocol. Loads a lightweight 82M-parameter
model at startup and synthesises speech on CPU via run_in_executor.
"""
import asyncio
import logging
import time
from functools import partial
from typing import Optional

import numpy as np

from backend.config import settings

logger = logging.getLogger("providers.local_tts")


class LocalTTSProvider:
    """
    Text-to-Speech via Kokoro (82M params, CPU-friendly).

    - Model + voice loaded once at startup.
    - synthesis runs in asyncio executor (CPU-bound).
    - Returns raw PCM bytes (16-bit signed, 24 kHz, mono).
    """

    def __init__(self) -> None:
        self._pipeline = None
        self._voice: str = settings.tts_voice
        self._sample_rate: int = settings.tts_sample_rate

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        if self._pipeline is not None:
            logger.warning("TTS model already loaded — skipping")
            return

        logger.info(f"Loading Kokoro TTS: voice={self._voice}")
        start = time.perf_counter()

        loop = asyncio.get_running_loop()

        def _init_kokoro():
            from kokoro import KPipeline
            return KPipeline(lang_code="a")  # 'a' = American English

        self._pipeline = await loop.run_in_executor(None, _init_kokoro)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"TTS model loaded in {elapsed:.0f}ms")

    def is_ready(self) -> bool:
        return self._pipeline is not None

    async def unload(self) -> None:
        self._pipeline = None
        logger.info("TTS model unloaded")

    # ── Synthesis ────────────────────────────────────────────

    async def synthesize(self, text: str) -> bytes:
        """
        Synthesise text to raw PCM audio bytes.

        :param text: Text to speak.
        :returns: PCM bytes (16-bit signed, 24 kHz, mono).
        """
        if self._pipeline is None:
            raise RuntimeError("TTS model not loaded — call load() first")

        if not text or not text.strip():
            return b""

        loop = asyncio.get_running_loop()
        start = time.perf_counter()

        def _synthesize():
            audio_segments = []
            for _, _, audio in self._pipeline(text, voice=self._voice):
                if audio is not None:
                    audio_segments.append(audio)

            if not audio_segments:
                return np.array([], dtype=np.float32)
            return np.concatenate(audio_segments)

        audio_np = await loop.run_in_executor(None, _synthesize)

        if len(audio_np) == 0:
            return b""

        # Convert float32 → int16 PCM bytes
        int16_audio = (audio_np * 32767).clip(-32768, 32767).astype(np.int16)
        pcm_bytes = int16_audio.tobytes()

        elapsed_ms = (time.perf_counter() - start) * 1000
        audio_duration_ms = (len(audio_np) / self._sample_rate) * 1000
        logger.info(
            f"TTS synthesised {audio_duration_ms:.0f}ms audio in {elapsed_ms:.0f}ms "
            f"(text_len={len(text)})"
        )

        return pcm_bytes
