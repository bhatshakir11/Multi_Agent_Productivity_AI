"""NewsAPI fetching logic for the News Agent."""

from __future__ import annotations

from html import unescape
import os
from typing import Any
import xml.etree.ElementTree as ET

import requests


NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
GOOGLE_NEWS_TECH_RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=technology&hl=en-US&gl=US&ceid=US:en"
)


class NewsFetchError(RuntimeError):
    """Raised when NewsAPI cannot return usable articles."""


def _read_config_value(name: str) -> str:
    """Read optional NewsAPI settings from config.py."""
    try:
        import config  # type: ignore

        value = getattr(config, name, "")
        return str(value) if value else ""
    except Exception:
        return ""


def get_news_api_key() -> str:
    """Return the NewsAPI key from environment variables or config.py."""
    api_key = os.getenv("NEWS_API_KEY") or _read_config_value("NEWS_API_KEY")

    if not api_key:
        raise NewsFetchError("Missing NEWS_API_KEY.")

    return api_key


def _clean_text(value: str | None) -> str:
    """Normalize text from JSON or RSS feeds."""
    return unescape(value or "").strip()


def _fetch_from_google_news_rss(page_size: int = 5) -> list[dict[str, str]]:
    """Fallback tech news provider when NewsAPI is unreachable."""
    try:
        response = requests.get(GOOGLE_NEWS_TECH_RSS_URL, timeout=20)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise NewsFetchError("Google News RSS request timed out.") from exc
    except requests.RequestException as exc:
        raise NewsFetchError(f"Google News RSS network error: {exc}") from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise NewsFetchError("Google News RSS returned invalid XML.") from exc

    articles: list[dict[str, str]] = []
    for item in root.findall("./channel/item")[:page_size]:
        title = _clean_text(item.findtext("title"))
        url = _clean_text(item.findtext("link"))
        published_at = _clean_text(item.findtext("pubDate"))
        source_node = item.find("source")
        source = _clean_text(source_node.text if source_node is not None else "")

        articles.append(
            {
                "title": title or "Untitled",
                "description": title,
                "source": source or "Google News",
                "url": url,
                "published_at": published_at,
            }
        )

    return articles


def _fetch_from_newsapi(page_size: int = 5) -> list[dict[str, str]]:
    """Fetch top English technology headlines from NewsAPI."""
    params = {
        "category": "technology",
        "language": "en",
        "pageSize": page_size,
        "apiKey": get_news_api_key(),
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=20)
        response_json: dict[str, Any] = response.json()
    except requests.Timeout as exc:
        raise NewsFetchError("NewsAPI request timed out.") from exc
    except requests.RequestException as exc:
        raise NewsFetchError(f"NewsAPI network error: {exc}") from exc
    except ValueError as exc:
        raise NewsFetchError("NewsAPI returned a non-JSON response.") from exc

    if not response.ok or response_json.get("status") != "ok":
        message = response_json.get("message", response.text)
        raise NewsFetchError(f"NewsAPI error: {message}")

    articles = response_json.get("articles", [])
    clean_articles: list[dict[str, str]] = []

    for article in articles:
        clean_articles.append(
            {
                "title": _clean_text(article.get("title") or "Untitled"),
                "description": _clean_text(article.get("description") or ""),
                "source": _clean_text(article.get("source", {}).get("name") or ""),
                "url": _clean_text(article.get("url") or ""),
                "published_at": _clean_text(article.get("publishedAt") or ""),
            }
        )

    return clean_articles


def fetch_top_tech_news(page_size: int = 5) -> list[dict[str, str]]:
    """Fetch top technology headlines with a fallback provider.

    NewsAPI remains the primary source. If DNS/network/API access fails, the
    agent falls back to Google News RSS so the daily summary can still include
    technology headlines.
    """
    try:
        return _fetch_from_newsapi(page_size=page_size)
    except NewsFetchError as newsapi_error:
        print(f"NewsAPI warning: {newsapi_error}. Falling back to Google News RSS.")
        return _fetch_from_google_news_rss(page_size=page_size)
