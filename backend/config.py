"""
Application configuration via Pydantic BaseSettings.
All config loaded from environment variables.
"""
from typing import Literal, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI Backend
    ai_backend: Literal["local", "cloud", "groq"] = "groq"
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Database (Phase 3)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_interview"
    postgres_user: str = "postgres"
    postgres_password: str = "changeme"

    # Redis (Phase 3)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # ── STT Settings ─────────────────────────────────────────
    stt_model_size: str = "distil-small.en"
    stt_compute_type: str = "int8"

    # ── LLM Settings ─────────────────────────────────────────
    llm_model_path: str = "models/qwen3.5-9b-q4_k_m.gguf"
    llm_gpu_layers: int = -1
    llm_context_size: int = 8192
    llm_n_threads: int = 6
    llm_temperature: float = 0.5
    llm_max_tokens: int = 512
    max_concurrent_llm_sessions: int = 1

    # ── TTS Settings ─────────────────────────────────────────
    tts_voice: str = "af_heart"
    tts_sample_rate: int = 24000

    # ── Cloud API Keys ───────────────────────────────────────
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None

    # Other settings
    cors_origins: str = "http://localhost:4200"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": ""
    }


settings = Settings()
