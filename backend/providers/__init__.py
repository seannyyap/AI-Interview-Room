"""
Provider Factory — instantiates the correct AI provider based on config.

Reads `settings.ai_backend` ("local" | "cloud") and returns the
appropriate STT, LLM, and TTS provider instances.
"""
import logging
from typing import Tuple

from backend.config import settings
from backend.services.interfaces import STTProvider, LLMProvider, TTSProvider

logger = logging.getLogger("providers")


def get_stt_provider() -> STTProvider:
    """Create an STT provider based on AI_BACKEND config."""
    if settings.ai_backend == "cloud":
        from backend.providers.cloud_stt import CloudSTTProvider
        logger.info("Using Cloud STT provider (Deepgram)")
        return CloudSTTProvider()
    else:
        from backend.providers.local_stt import LocalSTTProvider
        logger.info("Using Local STT provider (faster-whisper)")
        return LocalSTTProvider()


def get_llm_provider() -> LLMProvider:
    """Create an LLM provider based on AI_BACKEND config."""
    if settings.ai_backend == "cloud":
        from backend.providers.cloud_llm import CloudLLMProvider
        logger.info("Using Cloud LLM provider (OpenAI)")
        return CloudLLMProvider()
    elif settings.ai_backend == "ollama":
        from backend.providers.ollama_llm import OllamaLLMProvider
        logger.info("Using Ollama LLM provider")
        return OllamaLLMProvider()
    else:
        from backend.providers.local_llm import LocalLLMProvider
        logger.info("Using Local LLM provider (llama-cpp-python)")
        return LocalLLMProvider()


def get_tts_provider() -> TTSProvider:
    """Create a TTS provider based on AI_BACKEND config."""
    if settings.ai_backend == "cloud":
        from backend.providers.cloud_tts import CloudTTSProvider
        logger.info("Using Cloud TTS provider (ElevenLabs)")
        return CloudTTSProvider()
    else:
        from backend.providers.local_tts import LocalTTSProvider
        logger.info("Using Local TTS provider (Kokoro)")
        return LocalTTSProvider()


def get_all_providers() -> Tuple[STTProvider, LLMProvider, TTSProvider]:
    """Convenience: create all three providers at once."""
    return get_stt_provider(), get_llm_provider(), get_tts_provider()
