"""SQLite reminder creation utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path


# create_reminder.py -> reminder_agent -> agents -> productivity_ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "app.db"


class ReminderAgentError(RuntimeError):
    """Raised when reminder storage or workflow operations fail."""


def get_database_connection() -> sqlite3.Connection:
    """Open the shared SQLite database with row dictionaries enabled."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_reminders_table() -> None:
    """Create the reminders table if it does not exist."""
    try:
        with get_database_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    due_time TEXT,
                    status TEXT
                )
                """
            )
    except sqlite3.Error as exc:
        raise ReminderAgentError(f"Failed to initialize reminders table: {exc}") from exc


def create_reminder(
    title: str,
    due_time: str,
    status: str = "pending",
) -> dict[str, str | int]:
    """Create a reminder and return the stored reminder record."""
    if not title or not title.strip():
        raise ReminderAgentError("Reminder title cannot be empty.")

    if not due_time or not due_time.strip():
        raise ReminderAgentError("Reminder due_time cannot be empty.")

    initialize_reminders_table()

    try:
        with get_database_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reminders (title, due_time, status)
                VALUES (?, ?, ?)
                """,
                (title.strip(), due_time.strip(), status.strip()),
            )
            reminder_id = cursor.lastrowid
    except sqlite3.Error as exc:
        raise ReminderAgentError(f"Failed to create reminder: {exc}") from exc

    return {
        "id": int(reminder_id),
        "title": title.strip(),
        "due_time": due_time.strip(),
        "status": status.strip(),
    }
