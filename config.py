"""Shared project configuration.

Secrets are read from environment variables so they do not need to be committed
to source control. Individual agents can import these values while still being
safe to reuse in schedulers, CLIs, or future orchestrators.
"""

from __future__ import annotations

import os


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "moonshotai/kimi-k2.6")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_TIMEOUT_SECONDS = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "90"))
