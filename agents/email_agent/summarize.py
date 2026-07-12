"""NVIDIA-powered email summarization utilities."""

from __future__ import annotations

from utils.ai_client import AIClientError, ask_ai



class NvidiaAgentError(RuntimeError):
    """Raised when the NVIDIA API cannot complete an agent request."""


def ask_nvidia(
    prompt: str,
    *,
    max_tokens: int = 220,
    temperature: float = 0.2,
    top_p: float = 0.7,
) -> str:
    """Compatibility wrapper used by existing email agent modules."""
    try:
        return ask_ai(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    except AIClientError as exc:
        raise NvidiaAgentError(str(exc)) from exc


def summarize_email(text: str) -> str:
    """Summarize an email into two concise lines."""
    if not text or not text.strip():
        return "No readable email content available."

    prompt = f"""
Summarize this email in exactly 2 concise lines.
Focus on what happened and what the recipient should know.
Do not add labels, bullets, or extra commentary.

Email:
{text[:6000]}
"""
    return ask_nvidia(prompt, max_tokens=120, temperature=0.2)
