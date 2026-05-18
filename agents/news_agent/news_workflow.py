"""End-to-end workflow for the News Agent.

Run from the productivity_ai directory:
    python -m agents.news_agent.news_workflow
"""

from __future__ import annotations

import os
import sys

from agents.news_agent.fetch_news import NewsFetchError, fetch_top_tech_news
from agents.news_agent.summarize_news import NewsSummaryError, summarize_article
from notifications.telegram import TelegramNotificationError, send_telegram_message


try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def build_news_digest(items: list[dict[str, str]]) -> str:
    """Build a Telegram-ready news digest message."""
    if not items:
        return "TOP TECH NEWS TODAY\n\nNo technology news found."

    lines = ["TOP TECH NEWS TODAY", ""]

    for index, item in enumerate(items, 1):
        lines.append(f"{index}. {item['title']}")
        lines.append(item["summary"])

        if item.get("url"):
            lines.append(item["url"])

        lines.append("")

    lines.append("#AI #Technology")
    return "\n".join(lines).strip()


def fallback_article_summary(article: dict[str, str]) -> str:
    """Create a readable local summary when AI summarization is unavailable."""
    text = article.get("description") or article.get("title") or "No article details available."
    compact = " ".join(text.split())

    if len(compact) > 260:
        compact = compact[:257].rstrip() + "..."

    return compact


def run_news_agent(page_size: int | None = None) -> str:
    """Fetch, summarize, print, send, and return a tech news digest."""
    page_size = page_size or int(os.getenv("NEWS_AGENT_PAGE_SIZE", "5"))

    try:
        articles = fetch_top_tech_news(page_size=page_size)
    except NewsFetchError as exc:
        message = f"News Agent fetch error: {exc}"
        print(message)
        return message

    summarized_items: list[dict[str, str]] = []
    for article in articles:
        try:
            summary = summarize_article(article)
        except NewsSummaryError as exc:
            summary = fallback_article_summary(article)
            print(f"News Agent AI warning: {exc}")

        summarized_items.append({**article, "summary": summary})

    digest = build_news_digest(summarized_items)
    print(digest)

    try:
        send_telegram_message(digest)
        print("Telegram news digest sent.")
    except TelegramNotificationError as exc:
        print(f"News Agent Telegram warning: {exc}")

    return digest


if __name__ == "__main__":
    run_news_agent()
