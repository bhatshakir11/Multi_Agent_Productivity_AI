"""Shared project configuration.

Secrets are read from environment variables or .env file using Pydantic Settings,
so they do not need to be committed to source control.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    news_api_key: str = Field(default="", alias="NEWS_API_KEY")

    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nvidia_nim_api_key: str = Field(default="", alias="NVIDIA_NIM_API_KEY")
    nvidia_model: str = Field(default="moonshotai/kimi-k2.6", alias="NVIDIA_MODEL")
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL"
    )
    nvidia_timeout_seconds: float = Field(default=90.0, alias="NVIDIA_TIMEOUT_SECONDS")


# Initialize global settings instance
settings = Settings()

# Backwards compatibility layer
TELEGRAM_BOT_TOKEN = settings.telegram_bot_token
TELEGRAM_CHAT_ID = settings.telegram_chat_id
NEWS_API_KEY = settings.news_api_key
NVIDIA_API_KEY = settings.nvidia_api_key
NVIDIA_NIM_API_KEY = settings.nvidia_nim_api_key
NVIDIA_MODEL = settings.nvidia_model
NVIDIA_BASE_URL = settings.nvidia_base_url
NVIDIA_TIMEOUT_SECONDS = settings.nvidia_timeout_seconds
