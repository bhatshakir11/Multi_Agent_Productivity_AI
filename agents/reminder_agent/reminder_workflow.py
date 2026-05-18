"""End-to-end workflow for the Reminder Agent.

Run from the productivity_ai directory:
    python -m agents.reminder_agent.reminder_workflow
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from agents.reminder_agent.create_reminder import ReminderAgentError, create_reminder
from agents.reminder_agent.fetch_reminders import fetch_pending_reminders
from agents.reminder_agent.reminder_scheduler import (
    check_and_send_due_reminders,
    run_scheduler_forever,
)


try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def print_reminder_created(reminder: dict[str, str | int]) -> None:
    """Print a clean reminder creation confirmation."""
    print("\n================================")
    print("REMINDER CREATED")
    print("\nTask:")
    print(reminder["title"])
    print("\nDue Time:")
    print(reminder["due_time"])
    print("================")


def print_pending_reminders(reminders: list[dict[str, str | int]]) -> None:
    """Print pending reminders for debugging and review."""
    if not reminders:
        print("No pending reminders.")
        return

    print("\nPENDING REMINDERS")
    for reminder in reminders:
        print(f"{reminder['id']}. {reminder['title']} - {reminder['due_time']}")


def run_reminder_agent(
    title: str | None = None,
    due_time: str | None = None,
    *,
    scheduler: bool = False,
    check_due: bool = False,
    list_pending: bool = False,
) -> dict[str, str | int] | list[dict[str, str | int]] | None:
    """Run one Reminder Agent workflow action."""
    try:
        if scheduler:
            run_scheduler_forever()
            return None

        if check_due:
            return check_and_send_due_reminders()

        if list_pending:
            reminders = fetch_pending_reminders()
            print_pending_reminders(reminders)
            return reminders

        if title and due_time:
            reminder = create_reminder(title, due_time)
            print_reminder_created(reminder)
            return reminder

        reminders = fetch_pending_reminders()
        print_pending_reminders(reminders)
        return reminders
    except ReminderAgentError as exc:
        print(f"Reminder Agent error: {exc}")
        return None


def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the Reminder Agent CLI parser."""
    parser = argparse.ArgumentParser(description="Run the Reminder Agent.")
    parser.add_argument("--title", help="Reminder title/task.")
    parser.add_argument(
        "--due",
        help="Due time in YYYY-MM-DD HH:MM format.",
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start the background scheduler and keep running.",
    )
    parser.add_argument(
        "--check-due",
        action="store_true",
        help="Check due reminders once and send notifications.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List pending reminders.",
    )
    return parser


def _validate_due_time(due_time: str) -> str:
    """Validate and normalize due time format."""
    try:
        return datetime.strptime(due_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ReminderAgentError("Due time must use YYYY-MM-DD HH:MM format.") from exc


def main() -> None:
    """CLI entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    due_time = _validate_due_time(args.due) if args.due else None

    run_reminder_agent(
        title=args.title,
        due_time=due_time,
        scheduler=args.scheduler,
        check_due=args.check_due,
        list_pending=args.list,
    )


if __name__ == "__main__":
    main()
