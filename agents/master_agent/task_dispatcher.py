"""Task dispatching from the Master Agent to specialist agents."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agents.calendar_agent.create_event import (
    DEFAULT_TIME_ZONE,
    CalendarAgentError,
    create_event,
)
from agents.calendar_agent.event_parser import parse_event_from_text
from agents.calendar_agent.fetch_events import fetch_todays_agenda
from agents.email_agent.email_workflow import fetch_today_email_summaries, run_email_agent
from agents.news_agent.fetch_news import fetch_top_tech_news
from agents.reminder_agent.create_reminder import ReminderAgentError, create_reminder
from agents.reminder_agent.fetch_reminders import fetch_pending_reminders
from agents.reminder_agent.reminder_scheduler import check_and_send_due_reminders
from notifications.telegram import TelegramNotificationError, send_telegram_message


class DispatchError(RuntimeError):
    """Raised when a dispatched task fails."""


def _parse_iso_datetime(value: str) -> datetime:
    """Parse ISO datetime values returned by Calendar Agent utilities."""
    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(DEFAULT_TIME_ZONE))

    return parsed


def _reminder_time_before_event(start_time: str, minutes_before: int = 30) -> str:
    """Return reminder due time formatted for the Reminder Agent database."""
    start = _parse_iso_datetime(start_time)
    reminder_time = start - timedelta(minutes=minutes_before)
    return reminder_time.strftime("%Y-%m-%d %H:%M")


def dispatch_email_agent(max_results: int = 1):
    """Run the Email Agent workflow."""
    return run_email_agent(max_results=max_results)


def dispatch_today_email_summaries(limit: int = 5) -> list[dict[str, str]]:
    """Fetch today's summarized Important/College/Work emails via Email Agent."""
    return fetch_today_email_summaries(limit=limit)


def dispatch_calendar_event_from_text(text: str) -> dict[str, str]:
    """Parse text and create a Calendar event without duplicating Calendar logic."""
    try:
        parsed = parse_event_from_text(text)
        event = create_event(
            parsed["title"],
            parsed["start_time"],
            parsed["end_time"],
            description=parsed.get("description", ""),
        )
        event["priority"] = parsed.get("priority", "Medium")
        return event
    except CalendarAgentError as exc:
        raise DispatchError(f"Calendar dispatch failed: {exc}") from exc


def dispatch_reminder_for_event(
    event: dict[str, str],
    *,
    minutes_before: int = 30,
) -> dict[str, str | int]:
    """Create a reminder before a Calendar event."""
    title = f"Upcoming event: {event.get('title', 'Calendar Event')}"
    start_time = event.get("start_time", "")

    if not start_time:
        raise DispatchError("Cannot create reminder because event start_time is missing.")

    due_time = _reminder_time_before_event(start_time, minutes_before=minutes_before)

    try:
        return create_reminder(title, due_time)
    except ReminderAgentError as exc:
        raise DispatchError(f"Reminder dispatch failed: {exc}") from exc


def dispatch_due_reminder_check():
    """Run one due-reminder check."""
    return check_and_send_due_reminders()


def dispatch_todays_events() -> list[dict[str, str]]:
    """Fetch today's Calendar events."""
    try:
        return fetch_todays_agenda()
    except CalendarAgentError as exc:
        raise DispatchError(f"Calendar agenda fetch failed: {exc}") from exc


def dispatch_pending_reminders() -> list[dict[str, str | int]]:
    """Fetch pending reminders."""
    try:
        return fetch_pending_reminders()
    except ReminderAgentError as exc:
        raise DispatchError(f"Reminder fetch failed: {exc}") from exc


def dispatch_top_news(page_size: int = 1) -> list[dict[str, str]]:
    """Fetch top technology news headlines for the daily summary."""
    return fetch_top_tech_news(page_size=page_size)


def dispatch_notification(message: str) -> dict[str, str]:
    """Send a Master Agent notification through Telegram."""
    results: dict[str, str] = {}

    try:
        send_telegram_message(message)
        results["telegram"] = "sent"
    except TelegramNotificationError as exc:
        results["telegram"] = f"failed: {exc}"

    return results
