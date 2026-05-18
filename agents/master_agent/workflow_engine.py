"""Sequential workflow engine for the Master Agent."""

from __future__ import annotations

from datetime import datetime

from agents.master_agent.shared_context import SharedContext
from agents.master_agent.task_dispatcher import (
    DispatchError,
    dispatch_calendar_event_from_text,
    dispatch_due_reminder_check,
    dispatch_notification,
    dispatch_pending_reminders,
    dispatch_reminder_for_event,
    dispatch_todays_events,
    dispatch_today_email_summaries,
    dispatch_top_news,
)


EMAIL_TO_CALENDAR_REMINDER_WORKFLOW = "EMAIL_TO_CALENDAR_REMINDER_WORKFLOW"
CALENDAR_EVENT_TO_REMINDER_WORKFLOW = "CALENDAR_EVENT_TO_REMINDER_WORKFLOW"
DAILY_SUMMARY_WORKFLOW = "DAILY_SUMMARY_WORKFLOW"
REMINDER_CHECK_WORKFLOW = "REMINDER_CHECK_WORKFLOW"


def _format_time(raw_time: str) -> str:
    """Format an ISO datetime or date string for compact reports."""
    if not raw_time:
        return "Any time"

    try:
        parsed = datetime.fromisoformat(raw_time)
        return parsed.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return raw_time


def format_event_orchestration_message(
    event: dict[str, str],
    reminder: dict[str, str | int],
) -> str:
    """Build notification text for event + reminder orchestration."""
    return f"""MASTER AGENT WORKFLOW COMPLETE

Calendar Event:
{event.get('title', 'Untitled Event')}

Start:
{event.get('start_time', '')}

Reminder:
{reminder.get('title', '')}

Reminder Time:
{reminder.get('due_time', '')}"""


def run_email_to_calendar_reminder_workflow(text: str) -> SharedContext:
    """Route detected event text into Calendar and Reminder agents."""
    context = SharedContext(
        workflow_name=EMAIL_TO_CALENDAR_REMINDER_WORKFLOW,
        input_text=text,
        intent="calendar_event_with_reminder",
    )

    try:
        event = dispatch_calendar_event_from_text(text)
        context.set("calendar_event", event)

        reminder = dispatch_reminder_for_event(event, minutes_before=30)
        context.set("reminder", reminder)

        notification = format_event_orchestration_message(event, reminder)
        context.set("notification_results", dispatch_notification(notification))
    except DispatchError as exc:
        context.add_error(str(exc))

    return context


def run_calendar_event_to_reminder_workflow(
    event: dict[str, str],
    *,
    minutes_before: int = 30,
) -> SharedContext:
    """Create a reminder for an existing Calendar event."""
    context = SharedContext(
        workflow_name=CALENDAR_EVENT_TO_REMINDER_WORKFLOW,
        intent="calendar_event_to_reminder",
    )
    context.set("calendar_event", event)

    try:
        reminder = dispatch_reminder_for_event(event, minutes_before=minutes_before)
        context.set("reminder", reminder)
    except DispatchError as exc:
        context.add_error(str(exc))

    return context


def format_daily_productivity_summary(
    email_summaries: list[dict[str, str]],
    events: list[dict[str, str]],
    reminders: list[dict[str, str | int]],
    news_items: list[dict[str, str]],
) -> str:
    """Build the combined daily productivity summary."""
    lines = ["\U0001f4c5 DAILY PRODUCTIVITY SUMMARY", "", "\U0001f4e7 Today's Emails:", ""]

    if not email_summaries:
        lines.append("* No important, college, or work emails found today")
    else:
        for email in email_summaries[:5]:
            lines.append(f"* {email['subject']}")
            lines.append(email["summary"])
            lines.append("")

    lines.extend(["\U0001f4c5 Today's Events:", ""])

    if not events:
        lines.append("* No events scheduled")
    else:
        for event in events:
            lines.append(f"* {event['title']} - {_format_time(event['start_time'])}")

    lines.extend(["", "\u23f0 Pending Reminders:", ""])

    if not reminders:
        lines.append("* No pending reminders")
    else:
        for reminder in reminders[:5]:
            lines.append(f"* {reminder['title']} - {reminder['due_time']}")

    lines.extend(["", "\U0001f4f0 Top Tech News:", ""])

    if not news_items:
        lines.append("* No tech news available")
    else:
        for item in news_items[:5]:
            lines.append(f"* {item['title']}")

    return "\n".join(lines)


def run_daily_summary_workflow(news_page_size: int = 5) -> SharedContext:
    """Run Email, Calendar, Reminder, News, then send one combined report."""
    context = SharedContext(
        workflow_name=DAILY_SUMMARY_WORKFLOW,
        intent="daily_summary",
    )

    email_summaries: list[dict[str, str]] = []
    events: list[dict[str, str]] = []
    reminders: list[dict[str, str | int]] = []
    news_items: list[dict[str, str]] = []

    try:
        email_summaries = dispatch_today_email_summaries(limit=5)
    except Exception as exc:
        context.add_error(f"Email summary workflow failed: {exc}")

    try:
        events = dispatch_todays_events()
    except DispatchError as exc:
        context.add_error(str(exc))

    try:
        reminders = dispatch_pending_reminders()
    except DispatchError as exc:
        context.add_error(str(exc))

    try:
        news_items = dispatch_top_news(page_size=news_page_size)
    except Exception as exc:
        context.add_error(f"News workflow failed: {exc}")

    summary = format_daily_productivity_summary(
        email_summaries,
        events,
        reminders,
        news_items,
    )
    context.set("email_summaries", email_summaries)
    context.set("events", events)
    context.set("reminders", reminders)
    context.set("news_items", news_items)
    context.set("daily_summary", summary)
    context.set("notification_results", dispatch_notification(summary))

    return context


def run_reminder_check_workflow() -> SharedContext:
    """Run one due-reminder check through the Reminder Agent."""
    context = SharedContext(
        workflow_name=REMINDER_CHECK_WORKFLOW,
        intent="reminder_check",
    )

    try:
        context.set("sent_reminders", dispatch_due_reminder_check())
    except Exception as exc:
        context.add_error(f"Reminder check failed: {exc}")

    return context
