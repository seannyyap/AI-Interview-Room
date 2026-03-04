"""
Groq LLM Provider — High-speed cloud inference.

Implements LLMProvider protocol. Connects to the Groq API
for near-instantaneous token generation using open-source models.
"""
import json
import logging
import time
from typing import AsyncIterator, Dict, List, Optional

import httpx
from backend.config import settings

logger = logging.getLogger("providers.groq_llm")

class GroqLLMProvider:
    """
    LLM inference via Groq's extremely fast LPU API.
    """

    def __init__(self) -> None:
        self._api_key = settings.groq_api_key
        self._model_name = settings.groq_model
        # Groq uses an OpenAI-compatible endpoint structure
        self._url = "https://api.groq.com/openai/v1/chat/completions"
        self._is_ready = False

    async def load(self) -> None:
        """
        Verify Groq API key is present.
        """
        if not self._api_key:
            logger.error("GROQ_API_KEY is not set in environment or config.")
            self._is_ready = False
            return
            
        logger.info(f"Connecting to Groq API (model: {self._model_name})...")
        self._is_ready = True
        logger.info("Groq LLM Provider ready")

    def is_ready(self) -> bool:
        return self._is_ready

    async def unload(self) -> None:
        self._is_ready = False
        logger.info("Groq LLM Provider unloaded")

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream LLM tokens from Groq API.
        """
        if not self._is_ready:
            raise RuntimeError("Groq LLM provider not ready (missing API key?)")

        temperature = kwargs.get("temperature", settings.llm_temperature)
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": kwargs.get("max_tokens", settings.llm_max_tokens),
        }

        start = time.perf_counter()
        first_token_time: Optional[float] = None
        token_count = 0

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self._url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Groq API error: {response.status_code} - {error_text.decode()}")
                        yield "I'm sorry, my remote brain is having some trouble connecting."
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                            
                        data_str = line[6:] # Strip "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                            
                        try:
                            chunk = json.loads(data_str)
                            if chunk.get("choices") and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                token = delta.get("content", "")
                                
                                if token:
                                    if first_token_time is None:
                                        first_token_time = time.perf_counter()
                                        ttft_ms = (first_token_time - start) * 1000
                                        logger.info(f"Groq time-to-first-token: {ttft_ms:.0f}ms")
                                    
                                    token_count += 1
                                    yield token
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON from Groq stream: {data_str}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error during Groq generation: {e}", exc_info=True)
            yield "[Error: Lost connection to Groq]"

        total_ms = (time.perf_counter() - start) * 1000
        tps = (token_count / (total_ms / 1000)) if total_ms > 0 else 0
        logger.info(
            f"Groq generated {token_count} tokens in {total_ms:.0f}ms "
            f"({tps:.1f} tok/s)"
        )
