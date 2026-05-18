"""Reminder notification utilities."""

from __future__ import annotations

from agents.reminder_agent.create_reminder import ReminderAgentError
from notifications.telegram import TelegramNotificationError, send_telegram_message


def format_reminder_message(reminder: dict[str, str | int]) -> str:
    """Build the reminder alert message."""
    return f"""\u23f0 REMINDER

Task:
{reminder['title']}

Due Time:
{reminder['due_time']}"""


def send_reminder_notification(reminder: dict[str, str | int]) -> dict[str, str]:
    """Send one reminder through Telegram."""
    message = format_reminder_message(reminder)
    results: dict[str, str] = {}

    try:
        send_telegram_message(message)
        results["telegram"] = "sent"
    except TelegramNotificationError as exc:
        results["telegram"] = f"failed: {exc}"

    if not any(value.startswith("sent") for value in results.values()):
        raise ReminderAgentError(
            "Reminder notification failed on all channels: "
            f"Telegram={results.get('telegram')}"
        )

    return results


def print_reminder_sent(
    reminder: dict[str, str | int],
    notification_results: dict[str, str],
) -> None:
    """Print a clean reminder sent status."""
    sent_channels = [
        channel.title()
        for channel, result in notification_results.items()
        if result.startswith("sent")
    ]

    print("\n================================")
    print("REMINDER SENT")
    print("\nTask:")
    print(reminder["title"])
    print("\nNotification:")
    print(" + ".join(sent_channels) if sent_channels else "None")
    print("===================")
