"""APScheduler integration for the Reminder Agent."""

from __future__ import annotations

import time

from apscheduler.schedulers.background import BackgroundScheduler

from agents.reminder_agent.create_reminder import ReminderAgentError
from agents.reminder_agent.fetch_reminders import (
    fetch_due_reminders,
    update_reminder_status,
)
from agents.reminder_agent.send_reminder import (
    print_reminder_sent,
    send_reminder_notification,
)


def check_and_send_due_reminders() -> list[dict[str, str | int]]:
    """Send due reminders and mark successfully notified reminders as sent."""
    due_reminders = fetch_due_reminders()
    sent_reminders: list[dict[str, str | int]] = []

    for reminder in due_reminders:
        try:
            notification_results = send_reminder_notification(reminder)
            update_reminder_status(int(reminder["id"]), "sent")
            print_reminder_sent(reminder, notification_results)
            sent_reminders.append(reminder)
        except ReminderAgentError as exc:
            print(f"Reminder Agent warning: {exc}")

    return sent_reminders


def start_reminder_scheduler(interval_minutes: int = 1) -> BackgroundScheduler:
    """Start the background reminder scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_and_send_due_reminders,
        "interval",
        minutes=interval_minutes,
        id="reminder_due_check",
        replace_existing=True,
    )
    scheduler.start()
    print(f"Reminder scheduler started. Checking every {interval_minutes} minute(s).")
    return scheduler


def run_scheduler_forever(interval_minutes: int = 1) -> None:
    """Run the scheduler until the process is interrupted."""
    scheduler = start_reminder_scheduler(interval_minutes=interval_minutes)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Reminder scheduler stopped.")
