"""
Cloud LLM Provider — OpenAI API with streaming.

Implements LLMProvider protocol. Streams tokens from OpenAI's
chat completions endpoint.
"""
import logging
import time
from typing import AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger("providers.cloud_llm")


class CloudLLMProvider:
    """
    LLM inference via OpenAI API (GPT-4o / GPT-4o-mini).

    Streams tokens via the async client.
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None
        self._model_name: str = settings.openai_model

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set — cannot use cloud LLM")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info(f"Cloud LLM provider ready (OpenAI {self._model_name})")

    def is_ready(self) -> bool:
        return self._client is not None

    async def unload(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        logger.info("Cloud LLM provider closed")

    # ── Inference ────────────────────────────────────────────

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """Stream tokens from OpenAI's chat completions API."""
        if self._client is None:
            raise RuntimeError("Cloud LLM not loaded — call load() first")

        temperature = kwargs.get("temperature", settings.llm_temperature)
        max_tokens = kwargs.get("max_tokens", settings.llm_max_tokens)

        start = time.perf_counter()
        first_token_time: Optional[float] = None
        token_count = 0

        stream = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            content = delta.content if delta else None
            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                    ttft_ms = (first_token_time - start) * 1000
                    # logger.info(f"Cloud LLM time-to-first-token: {ttft_ms:.0f}ms")

                token_count += 1
                yield content

        total_ms = (time.perf_counter() - start) * 1000
        # logger.info(f"Cloud LLM generated {token_count} tokens in {total_ms:.0f}ms")
