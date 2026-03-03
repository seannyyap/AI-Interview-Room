"""
Cloud TTS Provider — ElevenLabs API.

Implements TTSProvider protocol. Sends text to ElevenLabs and
returns PCM audio bytes.
"""
import logging
import time
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger("providers.cloud_tts")


class CloudTTSProvider:
    """
    Text-to-Speech via ElevenLabs REST API.

    Requires ELEVENLABS_API_KEY in environment / settings.
    Returns raw PCM bytes (from the mp3 response converted on-device,
    or we request pcm_24000 directly from ElevenLabs).
    """

    BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    # Rachel voice — professional female, good for interviews
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

    def __init__(self) -> None:
        self._api_key: str | None = settings.elevenlabs_api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._voice_id: str = self.DEFAULT_VOICE_ID

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        if not self._api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set — cannot use cloud TTS")
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info("Cloud TTS provider ready (ElevenLabs)")

    def is_ready(self) -> bool:
        return self._client is not None and bool(self._api_key)

    async def unload(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Cloud TTS provider closed")

    # ── Synthesis ────────────────────────────────────────────

    async def synthesize(self, text: str) -> bytes:
        """Send text to ElevenLabs and return raw PCM audio bytes."""
        if self._client is None:
            raise RuntimeError("Cloud TTS not loaded — call load() first")

        if not text or not text.strip():
            return b""

        start = time.perf_counter()

        response = await self._client.post(
            f"{self.BASE_URL}/{self._voice_id}",
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/pcm",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
            params={
                "output_format": "pcm_24000",
            },
        )
        response.raise_for_status()

        pcm_bytes = response.content
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"Cloud TTS synthesised {len(pcm_bytes)} bytes in {elapsed_ms:.0f}ms "
            f"(text_len={len(text)})"
        )

        return pcm_bytes
