"""
Local LLM Provider — llama-cpp-python with Vulkan GPU offload.

Implements LLMProvider protocol. Loads a GGUF model once at startup,
streams tokens via an async generator, and uses a semaphore to limit
concurrent GPU sessions.
"""
import asyncio
import logging
import time
from functools import partial
from typing import AsyncIterator, Dict, List, Optional


from backend.config import settings

logger = logging.getLogger("providers.local_llm")


class LocalLLMProvider:
    """
    LLM inference via llama-cpp-python with Vulkan GPU backend.

    - Model loaded once at startup (singleton).
    - Token streaming via async generator.
    - Concurrency limited by semaphore (GPU is a shared resource).
    """

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_llm_sessions)

    # ── Lifecycle ────────────────────────────────────────────

    async def load(self) -> None:
        if self._model is not None:
            logger.warning("LLM model already loaded — skipping")
            return

        logger.info(
            f"Loading LLM: path={settings.llm_model_path}, "
            f"gpu_layers={settings.llm_gpu_layers}, "
            f"n_ctx={settings.llm_context_size}, "
            f"n_threads={settings.llm_n_threads}"
        )
        start = time.perf_counter()

        loop = asyncio.get_running_loop()
        
        def _get_model_class():
            from llama_cpp import Llama
            return Llama

        LlamaClass = await loop.run_in_executor(None, _get_model_class)

        self._model = await loop.run_in_executor(
            None,
            partial(
                LlamaClass,
                model_path=settings.llm_model_path,
                n_gpu_layers=settings.llm_gpu_layers,
                n_threads=settings.llm_n_threads,
                n_ctx=settings.llm_context_size,
                verbose=False,
            ),
        )

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"LLM model loaded in {elapsed:.0f}ms")

    def is_ready(self) -> bool:
        return self._model is not None

    async def unload(self) -> None:
        self._model = None
        logger.info("LLM model unloaded")

    # ── Inference ────────────────────────────────────────────

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream LLM tokens for the given conversation history.

        Acquires a GPU semaphore to prevent concurrent sessions from
        exhausting VRAM. Uses run_in_executor to avoid blocking the
        event loop during token generation.
        """
        if self._model is None:
            raise RuntimeError("LLM model not loaded — call load() first")

        temperature = kwargs.get("temperature", settings.llm_temperature)
        max_tokens = kwargs.get("max_tokens", settings.llm_max_tokens)

        async with self._semaphore:
            loop = asyncio.get_running_loop()
            start = time.perf_counter()
            first_token_time: Optional[float] = None
            token_count = 0

            # Create the streaming generator in executor
            response = await loop.run_in_executor(
                None,
                partial(
                    self._model.create_chat_completion,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.9,
                    stream=True,
                ),
            )

            # Use a queue to bridge sync generator → async iterator
            # This avoids blocking the event loop on each token
            queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

            def _consume_stream():
                """Run in executor: read all tokens from the sync generator."""
                try:
                    for chunk in response:
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            queue.put_nowait(content)
                finally:
                    queue.put_nowait(None)  # Sentinel: stream finished

            # Start consuming the stream in a background thread
            consume_task = loop.run_in_executor(None, _consume_stream)

            try:
                while True:
                    token = await queue.get()
                    if token is None:
                        break

                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                        ttft_ms = (first_token_time - start) * 1000
                        logger.info(f"LLM time-to-first-token: {ttft_ms:.0f}ms")

                    token_count += 1
                    yield token
            finally:
                await consume_task

            total_ms = (time.perf_counter() - start) * 1000
            tps = (token_count / (total_ms / 1000)) if total_ms > 0 else 0
            logger.info(
                f"LLM generated {token_count} tokens in {total_ms:.0f}ms "
                f"({tps:.1f} tok/s)"
            )
