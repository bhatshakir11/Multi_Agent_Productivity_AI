"""End-to-end workflow for the Calendar Agent.

Run from the productivity_ai directory:
    python -m agents.calendar_agent.calendar_workflow
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agents.calendar_agent.create_event import (
    DEFAULT_TIME_ZONE,
    CalendarAgentError,
    create_event,
)
from agents.calendar_agent.event_parser import parse_event_from_text
from agents.calendar_agent.fetch_events import (
    fetch_agenda_for_days,
    fetch_events_for_date,
    fetch_todays_agenda,
    fetch_upcoming_events,
)
from notifications.telegram import TelegramNotificationError, send_telegram_message


try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def _format_event_time(raw_time: str) -> str:
    """Format an event start time for agenda messages."""
    if not raw_time:
        return "Any time"

    try:
        return datetime.fromisoformat(raw_time).strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return raw_time


def format_event_created_message(event: dict[str, str]) -> str:
    """Create a notification for a newly created event."""
    return f"""CALENDAR EVENT CREATED

TITLE:
{event.get('title', 'Untitled Event')}

START:
{event.get('start_time', '')}

END:
{event.get('end_time', '')}

DESCRIPTION:
{event.get('description', '') or 'None'}"""


def format_daily_agenda(events: list[dict[str, str]]) -> str:
    """Build today's schedule summary."""
    lines = ["\U0001f4c5 TODAY'S SCHEDULE", ""]

    if not events:
        lines.append("No events scheduled for today.")
        return "\n".join(lines)

    for event in events:
        lines.append(f"{_format_event_time(event['start_time'])} - {event['title']}")

    return "\n".join(lines)


def format_named_day_agenda(
    events: list[dict[str, str]],
    *,
    title: str,
) -> str:
    """Build a schedule summary for a named day."""
    lines = [f"\U0001f4c5 {title.upper()} SCHEDULE", ""]

    if not events:
        lines.append(f"No events scheduled for {title.lower()}.")
        return "\n".join(lines)

    for event in events:
        lines.append(f"{_format_event_time(event['start_time'])} - {event['title']}")

    return "\n".join(lines)


def format_multi_day_agenda(agenda: dict[str, list[dict[str, str]]]) -> str:
    """Build a grouped agenda summary across multiple days."""
    lines = ["\U0001f4c5 UPCOMING SCHEDULE", ""]

    for day, events in agenda.items():
        lines.append(day)

        if not events:
            lines.append("No events scheduled.")
        else:
            for event in events:
                lines.append(f"{_format_event_time(event['start_time'])} - {event['title']}")

        lines.append("")

    return "\n".join(lines).strip()


def notify_calendar_message(message: str) -> None:
    """Send a calendar notification through Telegram."""
    try:
        send_telegram_message(message)
        print("Calendar Agent Telegram sent.")
    except TelegramNotificationError as exc:
        print(f"Calendar Agent Telegram warning: {exc}")


def create_event_from_text(text: str) -> dict[str, str]:
    """Parse text, create a Calendar event, notify, and return the event."""
    parsed = parse_event_from_text(text)
    event = create_event(
        parsed["title"],
        parsed["start_time"],
        parsed["end_time"],
        description=parsed.get("description", ""),
    )
    event["priority"] = parsed.get("priority", "Medium")

    message = format_event_created_message(event)
    print(message)
    notify_calendar_message(message)
    return event


def send_daily_agenda() -> list[dict[str, str]]:
    """Fetch today's agenda and send it to configured notification channels."""
    events = fetch_todays_agenda()
    message = format_daily_agenda(events)
    print(message)
    notify_calendar_message(message)
    return events


def send_tomorrow_agenda() -> list[dict[str, str]]:
    """Fetch tomorrow's agenda and send it to configured notification channels."""
    tomorrow = datetime.now(ZoneInfo(DEFAULT_TIME_ZONE)).date() + timedelta(days=1)
    events = fetch_events_for_date(tomorrow)
    message = format_named_day_agenda(events, title="Tomorrow")
    print(message)
    notify_calendar_message(message)
    return events


def send_days_agenda(days: int) -> dict[str, list[dict[str, str]]]:
    """Fetch a multi-day agenda and send it to configured notification channels."""
    agenda = fetch_agenda_for_days(days=days)
    message = format_multi_day_agenda(agenda)
    print(message)
    notify_calendar_message(message)
    return agenda


def run_calendar_agent(
    text: str | None = None,
    *,
    agenda: bool = False,
    tomorrow: bool = False,
    days: int | None = None,
):
    """Run the Calendar Agent workflow.

    If text is provided, the agent creates an event. Otherwise it sends today's
    agenda, which is useful for schedulers and future coordinator agents.
    """
    try:
        if days:
            return send_days_agenda(days)

        if tomorrow:
            return send_tomorrow_agenda()

        if agenda or not text:
            return send_daily_agenda()

        return create_event_from_text(text)
    except CalendarAgentError as exc:
        print(f"Calendar Agent error: {exc}")
        return None


def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the Calendar Agent CLI parser."""
    parser = argparse.ArgumentParser(description="Run the Calendar Agent.")
    parser.add_argument(
        "text",
        nargs="*",
        help="Natural language event text, e.g. Project review tomorrow at 2 PM",
    )
    parser.add_argument(
        "--agenda",
        action="store_true",
        help="Send today's agenda instead of creating an event.",
    )
    parser.add_argument(
        "--tomorrow",
        action="store_true",
        help="Send tomorrow's agenda instead of creating an event.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Send a grouped agenda for N days starting today.",
    )
    parser.add_argument(
        "--upcoming",
        action="store_true",
        help="Print upcoming events without sending notifications.",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.upcoming:
        for event in fetch_upcoming_events():
            print(f"{event['start_time']} - {event['title']}")
        return

    text = " ".join(args.text).strip() or os.getenv("CALENDAR_EVENT_TEXT", "")
    run_calendar_agent(
        text=text or None,
        agenda=args.agenda,
        tomorrow=args.tomorrow,
        days=args.days,
    )


if __name__ == "__main__":
    main()
