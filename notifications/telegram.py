"""Reusable Telegram notification infrastructure.

Any agent can import send_telegram_message and send plain text alerts without
knowing Telegram's HTTP details.
"""

from __future__ import annotations

import os
from typing import Any

import requests


TELEGRAM_API_BASE_URL = "https://api.telegram.org"
DEFAULT_TIMEOUT_SECONDS = 20


class TelegramNotificationError(RuntimeError):
    """Raised when a Telegram notification cannot be sent."""


def _read_config_value(name: str) -> str:
    """Read optional Telegram settings from config.py."""
    try:
        import config  # type: ignore

        value = getattr(config, name, "")
        return str(value) if value else ""
    except Exception:
        return ""


def get_telegram_bot_token() -> str:
    """Return the Telegram bot token from env vars or config.py."""
    return os.getenv("TELEGRAM_BOT_TOKEN") or _read_config_value("TELEGRAM_BOT_TOKEN")


def get_telegram_chat_id() -> str:
    """Return the Telegram chat ID from env vars or config.py."""
    return os.getenv("TELEGRAM_CHAT_ID") or _read_config_value("TELEGRAM_CHAT_ID")


def send_telegram_message(
    message: str,
    *,
    chat_id: str | None = None,
    bot_token: str | None = None,
    parse_mode: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Send a text message through the Telegram Bot API.

    Args:
        message: Text to send.
        chat_id: Optional destination override. Defaults to TELEGRAM_CHAT_ID.
        bot_token: Optional bot token override. Defaults to TELEGRAM_BOT_TOKEN.
        parse_mode: Optional Telegram parse mode, such as Markdown or HTML.
        timeout: HTTP request timeout in seconds.

    Returns:
        Telegram API response JSON.
    """
    if not message or not message.strip():
        raise TelegramNotificationError("Telegram message cannot be empty.")

    resolved_token = bot_token or get_telegram_bot_token()
    resolved_chat_id = chat_id or get_telegram_chat_id()

    if not resolved_token:
        raise TelegramNotificationError(
            "Missing Telegram bot token. Set TELEGRAM_BOT_TOKEN."
        )

    if not resolved_chat_id:
        raise TelegramNotificationError("Missing Telegram chat ID. Set TELEGRAM_CHAT_ID.")

    url = f"{TELEGRAM_API_BASE_URL}/bot{resolved_token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": resolved_chat_id,
        "text": message.strip(),
        "disable_web_page_preview": True,
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response_json = response.json()
    except requests.Timeout as exc:
        raise TelegramNotificationError("Telegram request timed out.") from exc
    except requests.RequestException as exc:
        raise TelegramNotificationError(f"Telegram network error: {exc}") from exc
    except ValueError as exc:
        raise TelegramNotificationError("Telegram returned a non-JSON response.") from exc

    if not response.ok or not response_json.get("ok"):
        description = response_json.get("description", response.text)
        raise TelegramNotificationError(f"Telegram API error: {description}")

    return response_json
