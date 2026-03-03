"""
Ollama LLM Provider — Local inference via Ollama HTTP API.

Implements LLMProvider protocol. Connects to the local Ollama service
(running on host or in container) and streams tokens.
"""
import json
import logging
import time
from typing import AsyncIterator, Dict, List, Optional

import httpx
from backend.config import settings

logger = logging.getLogger("providers.ollama_llm")

class OllamaLLMProvider:
    """
    LLM inference via Ollama's HTTP API.
    """

    def __init__(self) -> None:
        self._url = f"{settings.ollama_base_url}/api/chat"
        self._model_name = settings.ollama_model
        self._is_ready = False

    async def load(self) -> None:
        """
        Verify Ollama is reachable and the model is pulled.
        """
        logger.info(f"Connecting to Ollama at {settings.ollama_base_url}...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if Ollama is running
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama returned status {resp.status_code}")
                
                # Check if model exists
                models = resp.json().get("models", [])
                model_exists = any(m["name"] == self._model_name for m in models)
                
                if not model_exists:
                    logger.warning(f"Model '{self._model_name}' not found locally in Ollama. Attempting to pull...")
                    # We could call /api/pull here, but for now we just log a warning 
                    # as pulling can take a long time and might timeout the startup.
                    logger.info(f"Please run 'ollama pull {self._model_name}' manually if this fails.")
                
                self._is_ready = True
                logger.info(f"Ollama LLM Provider ready (model: {self._model_name})")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            self._is_ready = False

    def is_ready(self) -> bool:
        return self._is_ready

    async def unload(self) -> None:
        self._is_ready = False
        logger.info("Ollama LLM Provider unloaded")

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream LLM tokens from Ollama.
        """
        if not self._is_ready:
            raise RuntimeError("Ollama LLM provider not ready")

        temperature = kwargs.get("temperature", settings.llm_temperature)
        
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": kwargs.get("max_tokens", settings.llm_max_tokens),
            }
        }

        start = time.perf_counter()
        first_token_time: Optional[float] = None
        token_count = 0

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self._url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Ollama API error: {response.status_code} - {error_text.decode()}")
                        yield "I'm sorry, I'm having trouble connecting to my brain right now."
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            token = chunk["message"]["content"]
                            if token:
                                if first_token_time is None:
                                    first_token_time = time.perf_counter()
                                    ttft_ms = (first_token_time - start) * 1000
                                    logger.info(f"Ollama time-to-first-token: {ttft_ms:.0f}ms")
                                
                                token_count += 1
                                yield token
                        
                        if chunk.get("done"):
                            break
        except Exception as e:
            logger.error(f"Error during Ollama generation: {e}")
            yield "[Error: Lost connection to Ollama]"

        total_ms = (time.perf_counter() - start) * 1000
        tps = (token_count / (total_ms / 1000)) if total_ms > 0 else 0
        logger.info(
            f"Ollama generated {token_count} tokens in {total_ms:.0f}ms "
            f"({tps:.1f} tok/s)"
        )
