from typing import Protocol, AsyncIterator, List, Dict, Any
import numpy as np


class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers."""

    async def load(self) -> None:
        """Load the model into memory. Called once at app startup."""
        ...

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio chunks into text.
        :param audio: Float32 numpy array of PCM audio.
        :param sample_rate: Audio sampling rate (e.g., 16000).
        """
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is loaded and ready for inference."""
        ...

    async def unload(self) -> None:
        """Release model resources. Called at app shutdown."""
        ...


class LLMProvider(Protocol):
    """Protocol for Large Language Model providers."""

    async def load(self) -> None:
        """Load the model into memory. Called once at app startup."""
        ...

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """
        Generate a response based on conversation history.
        :param messages: List of message dicts (OpenAI format).
        :yield: Generated text tokens.
        """
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is loaded and ready for inference."""
        ...

    async def unload(self) -> None:
        """Release model resources. Called at app shutdown."""
        ...


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers."""

    async def load(self) -> None:
        """Load the model/voice into memory. Called once at app startup."""
        ...

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to spoken audio.
        :param text: Text to synthesize.
        :return: Bytes of the generated audio (PCM 16-bit, 24kHz).
        """
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is loaded and ready for synthesis."""
        ...

    async def unload(self) -> None:
        """Release model resources. Called at app shutdown."""
        ...
