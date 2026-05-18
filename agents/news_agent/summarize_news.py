"""AI summarization logic for News Agent articles."""

from __future__ import annotations

from utils.ai_client import AIClientError, ask_ai


class NewsSummaryError(RuntimeError):
    """Raised when a news article cannot be summarized."""


def summarize_article(article: dict[str, str]) -> str:
    """Summarize one news article in two short lines."""
    title = article.get("title", "")
    description = article.get("description", "")

    if not title and not description:
        return "No article details available."

    prompt = f"""
Summarize this technology news in exactly 2 short lines.
Keep it useful for a busy productivity assistant user.
Do not add labels or extra commentary.

Title:
{title}

Description:
{description}
"""

    try:
        return ask_ai(prompt, max_tokens=120, temperature=0.3)
    except AIClientError as exc:
        raise NewsSummaryError(str(exc)) from exc
