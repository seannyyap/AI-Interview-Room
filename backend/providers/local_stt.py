"""
Local STT Provider — faster-whisper on CPU.

Implements STTProvider protocol. Loads a CTranslate2-optimized Whisper model
once at startup and runs transcription in a thread executor to avoid
blocking the async event loop.
"""
import asyncio
import logging
import re
import time
from functools import partial
from typing import Optional

import numpy as np

from backend.config import settings

logger = logging.getLogger("providers.local_stt")

# Regex patterns for sanitising Whisper hallucinations
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\S+@\S+\.\S+", re.IGNORECASE)


def _sanitize_transcript(text: str) -> str:
    """Strip hallucinated URLs and email addresses from Whisper output."""
    text = _URL_PATTERN.sub("", text)
    text = _EMAIL_PATTERN.sub("", text)
    return text.strip()


class LocalSTTProvider:
    """
    Speech-to-Text via faster-whisper (CTranslate2).

    - Model loaded once at startup (singleton).
    - Inference runs in asyncio executor (CPU-bound).
    - VAD filtering enabled to skip silence.
    """

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._model_size: str = settings.stt_model_size
        self._compute_type: str = settings.stt_compute_type

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        """Load the Whisper model. Runs in executor because it's slow."""
        if self._model is not None:
            logger.warning("STT model already loaded — skipping")
            return

        logger.info(
            f"Loading faster-whisper model: size={self._model_size}, "
            f"compute_type={self._compute_type}, device=auto"
        )
        start = time.perf_counter()

        loop = asyncio.get_running_loop()
        
        def _get_model_class():
            from faster_whisper import WhisperModel
            return WhisperModel

        WhisperModelClass = await loop.run_in_executor(None, _get_model_class)

        self._model = await loop.run_in_executor(
            None,
            partial(
                WhisperModelClass,
                self._model_size,
                device="auto",
                compute_type=self._compute_type,
            ),
        )

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"STT model loaded in {elapsed:.0f}ms")

    def is_ready(self) -> bool:
        return self._model is not None

    async def unload(self) -> None:
        self._model = None
        logger.info("STT model unloaded")

    # ── Inference ────────────────────────────────────────────

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe a PCM audio buffer to text.

        :param audio: Float32 numpy array.
        :param sample_rate: Expected to be 16 000 Hz.
        :returns: Transcribed and sanitised text.
        """
        if self._model is None:
            raise RuntimeError("STT model not loaded — call load() first")

        loop = asyncio.get_running_loop()
        start = time.perf_counter()

        def _transcribe_sync():
            """Run transcription AND segment materialisation in the executor thread."""
            segments, info = self._model.transcribe(
                audio,
                beam_size=2,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            # Materialise lazy generator inside executor — this is CPU-bound!
            text_parts = [seg.text for seg in segments]
            full_text = " ".join(text_parts).strip()
            return full_text, info

        full_text, info = await loop.run_in_executor(None, _transcribe_sync)

        elapsed_ms = (time.perf_counter() - start) * 1000
        audio_duration_ms = (len(audio) / sample_rate) * 1000
        
        # --- Noise / Hallucination Guard ---
        sanitized = _sanitize_transcript(full_text)
        
        # 1. Low confidence check (ignore weak noise triggers)
        if info.language_probability < 0.4 and len(sanitized) < 10:
            logger.info(f"STT: Ignored low confidence transcript ({info.language_probability:.2f})")
            return ""

        # 2. Hallucination filter (Whisper often transcribes noise as these)
        hallucinations = {"thank you.", "thanks for watching.", "please subscribe.", "okay.", "bye.", "you"}
        if sanitized.lower() in hallucinations and audio_duration_ms < 1500:
             logger.info(f"STT: Filtered potential hallucination: '{sanitized}'")
             return ""

        logger.info(
            f"STT transcribed {audio_duration_ms:.0f}ms audio in {elapsed_ms:.0f}ms "
            f"(lang={info.language}, prob={info.language_probability:.2f})"
        )

        return sanitized
