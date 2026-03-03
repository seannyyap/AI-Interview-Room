"""
Mock AI Providers — for testing and development without real models.

Each mock implements the same protocol + lifecycle as real providers.
"""
import asyncio
from typing import AsyncIterator, List, Dict

import numpy as np


class MockSTTProvider:
    """Mock STT provider that returns a dummy transcript."""

    async def load(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True

    async def unload(self) -> None:
        pass

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        await asyncio.sleep(0.1)
        duration_sec = len(audio) / sample_rate
        return f"[Mock transcript of {duration_sec:.1f}s audio at {sample_rate}Hz]"


class MockLLMProvider:
    """Mock LLM provider that streams a canned response."""

    async def load(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True

    async def unload(self) -> None:
        pass

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        last_message = messages[-1]["content"] if messages else ""
        response = (
            f"As your AI interviewer, I heard you say: '{last_message}'. "
            "That's an interesting point! Can you elaborate more on the technical "
            "trade-offs you considered when making that decision? "
            "For example, how does it affect scalability and maintainability?"
        )

        for word in response.split():
            await asyncio.sleep(0.05)
            yield word + " "


class MockTTSProvider:
    """Mock TTS provider — returns empty audio bytes."""

    async def load(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True

    async def unload(self) -> None:
        pass

    async def synthesize(self, text: str) -> bytes:
        await asyncio.sleep(0.1)
        return b""
