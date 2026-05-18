"""Shared NVIDIA AI client infrastructure.

Agents should call ask_ai instead of creating their own OpenAI clients. This
keeps model selection, API keys, timeouts, and error handling centralized.
"""

from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI, OpenAIError


class AIClientError(RuntimeError):
    """Raised when a shared AI request fails."""


def _read_config_value(name: str, default: str = "") -> str:
    """Read a value from config.py without making config mandatory."""
    try:
        import config  # type: ignore

        value = getattr(config, name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def get_nvidia_api_key() -> str:
    """Return the NVIDIA API key from environment variables or config.py."""
    api_key = (
        os.getenv("NVIDIA_API_KEY")
        or os.getenv("NVIDIA_NIM_API_KEY")
        or _read_config_value("NVIDIA_API_KEY")
        or _read_config_value("NVIDIA_NIM_API_KEY")
    )

    if not api_key:
        raise AIClientError("Missing NVIDIA API key. Set NVIDIA_API_KEY.")

    return api_key


def get_nvidia_model() -> str:
    """Return the configured NVIDIA model."""
    return (
        os.getenv("NVIDIA_MODEL")
        or _read_config_value("NVIDIA_MODEL")
        or "moonshotai/kimi-k2.6"
    )


def get_nvidia_base_url() -> str:
    """Return the NVIDIA OpenAI-compatible base URL."""
    return (
        os.getenv("NVIDIA_BASE_URL")
        or _read_config_value("NVIDIA_BASE_URL")
        or "https://integrate.api.nvidia.com/v1"
    )


def get_nvidia_timeout() -> float:
    """Return the NVIDIA client timeout in seconds."""
    raw_timeout = os.getenv("NVIDIA_TIMEOUT_SECONDS") or _read_config_value(
        "NVIDIA_TIMEOUT_SECONDS",
        "90",
    )
    try:
        return float(raw_timeout)
    except ValueError:
        return 90.0


@lru_cache(maxsize=1)
def get_ai_client() -> OpenAI:
    """Create one reusable OpenAI-compatible NVIDIA client per process."""
    return OpenAI(
        base_url=get_nvidia_base_url(),
        api_key=get_nvidia_api_key(),
        timeout=get_nvidia_timeout(),
    )


def ask_ai(
    prompt: str,
    *,
    system_prompt: str = "You are a concise productivity assistant.",
    model: str | None = None,
    max_tokens: int = 220,
    temperature: float = 0.2,
    top_p: float = 1.0,
) -> str:
    """Ask the configured NVIDIA model and return plain text content."""
    if not prompt or not prompt.strip():
        raise AIClientError("AI prompt cannot be empty.")

    try:
        response = get_ai_client().chat.completions.create(
            model=model or get_nvidia_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            extra_body={"chat_template_kwargs": {"thinking": False}},
        )
        return (response.choices[0].message.content or "").strip()
    except OpenAIError as exc:
        raise AIClientError(f"NVIDIA API request failed: {exc}") from exc
    except Exception as exc:
        raise AIClientError(f"Unexpected NVIDIA API failure: {exc}") from exc
