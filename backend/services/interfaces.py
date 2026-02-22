from typing import Protocol, AsyncIterator, List, Dict, Any
import numpy as np


class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers."""
    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio chunks into text.
        :param audio: Float32 numpy array of PCM audio.
        :param sample_rate: Audio sampling rate (e.g., 16000).
        """
        ...


class LLMProvider(Protocol):
    """Protocol for Large Language Model providers."""
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """
        Generate a response based on conversation history.
        :param messages: List of message dicts (OpenAI format).
        :yield: Generated text tokens.
        """
        ...


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers."""
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to spoken audio.
        :param text: Text to synthesize.
        :return: Bytes of the generated audio (PCM or WAV).
        """
        ...
