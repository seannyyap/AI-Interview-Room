"""
Application configuration via Pydantic BaseSettings.
All config loaded from environment variables.
"""
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI Backend
    ai_backend: Literal["local", "cloud"] = "local"
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

    # AI Models
    stt_model_size: str = "base"
    stt_compute_type: str = "int8"
    llm_model_path: str = "models/qwen2.5-7b-instruct-q4_k_m.gguf"
    llm_gpu_layers: int = -1
    llm_context_size: int = 4096

    # Other settings
    cors_origins: str = "http://localhost:4200"
    ai_backend: str = "local"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
