"""Intent routing for the Master Agent."""

from __future__ import annotations


CALENDAR_KEYWORDS = (
    "meeting",
    "review",
    "class",
    "appointment",
    "event",
    "call",
    "schedule",
)
REMINDER_KEYWORDS = ("remind", "reminder", "due", "deadline", "submit", "finish")
NEWS_KEYWORDS = ("news", "headline", "technology", "tech")
EMAIL_KEYWORDS = ("email", "gmail", "inbox")
SUMMARY_KEYWORDS = ("daily summary", "productivity summary", "today summary")


def route_intent(text: str) -> dict[str, object]:
    """Analyze incoming text and decide which workflow should run."""
    normalized = text.lower().strip()

    if not normalized:
        return {
            "intent": "daily_summary",
            "workflow": "DAILY_SUMMARY_WORKFLOW",
            "agents": ["calendar_agent", "reminder_agent", "news_agent"],
        }

    if any(keyword in normalized for keyword in SUMMARY_KEYWORDS):
        return {
            "intent": "daily_summary",
            "workflow": "DAILY_SUMMARY_WORKFLOW",
            "agents": ["calendar_agent", "reminder_agent", "news_agent"],
        }

    has_calendar_signal = any(keyword in normalized for keyword in CALENDAR_KEYWORDS)
    has_reminder_signal = any(keyword in normalized for keyword in REMINDER_KEYWORDS)
    has_time_signal = any(
        keyword in normalized
        for keyword in ("today", "tomorrow", "am", "pm", "morning", "evening")
    )

    if has_calendar_signal and has_time_signal:
        return {
            "intent": "calendar_event_with_reminder",
            "workflow": "EMAIL_TO_CALENDAR_REMINDER_WORKFLOW",
            "agents": ["calendar_agent", "reminder_agent", "notifications"],
        }

    if has_reminder_signal:
        return {
            "intent": "reminder",
            "workflow": "REMINDER_WORKFLOW",
            "agents": ["reminder_agent", "notifications"],
        }

    if any(keyword in normalized for keyword in NEWS_KEYWORDS):
        return {
            "intent": "news",
            "workflow": "NEWS_WORKFLOW",
            "agents": ["news_agent", "notifications"],
        }

    if any(keyword in normalized for keyword in EMAIL_KEYWORDS):
        return {
            "intent": "email",
            "workflow": "EMAIL_WORKFLOW",
            "agents": ["email_agent", "notifications"],
        }

    return {
        "intent": "daily_summary",
        "workflow": "DAILY_SUMMARY_WORKFLOW",
        "agents": ["calendar_agent", "reminder_agent", "news_agent"],
    }
