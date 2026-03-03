"""
Unit tests for Mock AI Providers — verify protocol compliance and lifecycle.
"""
import asyncio
import numpy as np
import pytest

from backend.providers.mock import MockSTTProvider, MockLLMProvider, MockTTSProvider


class TestMockSTTProvider:
    def test_is_ready_before_load(self):
        """Mock is always ready (no real model to load)."""
        provider = MockSTTProvider()
        assert provider.is_ready() is True

    @pytest.mark.asyncio
    async def test_transcribe_returns_string(self):
        provider = MockSTTProvider()
        await provider.load()
        audio = np.zeros(16000, dtype=np.float32)
        result = await provider.transcribe(audio, 16000)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_transcribe_includes_duration(self):
        provider = MockSTTProvider()
        await provider.load()
        audio = np.zeros(48000, dtype=np.float32)  # 3 seconds
        result = await provider.transcribe(audio, 16000)
        assert "3.0s" in result

    @pytest.mark.asyncio
    async def test_unload_lifecycle(self):
        provider = MockSTTProvider()
        await provider.load()
        await provider.unload()
        # Should not crash


class TestMockLLMProvider:
    @pytest.mark.asyncio
    async def test_generate_yields_tokens(self):
        provider = MockLLMProvider()
        await provider.load()
        messages = [{"role": "user", "content": "Hello"}]
        tokens = []
        async for token in provider.generate(messages):
            tokens.append(token)
        assert len(tokens) > 0

    @pytest.mark.asyncio
    async def test_generate_echoes_user_message(self):
        provider = MockLLMProvider()
        await provider.load()
        messages = [{"role": "user", "content": "test input"}]
        full_text = ""
        async for token in provider.generate(messages):
            full_text += token
        assert "test input" in full_text


class TestMockTTSProvider:
    @pytest.mark.asyncio
    async def test_synthesize_returns_bytes(self):
        provider = MockTTSProvider()
        await provider.load()
        result = await provider.synthesize("Hello world")
        assert isinstance(result, bytes)
