"""SQLite reminder fetching and status update utilities."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from agents.reminder_agent.create_reminder import (
    ReminderAgentError,
    get_database_connection,
    initialize_reminders_table,
)


def _row_to_dict(row: sqlite3.Row) -> dict[str, str | int]:
    """Convert a SQLite row into a plain reminder dictionary."""
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "due_time": str(row["due_time"]),
        "status": str(row["status"]),
    }


def fetch_pending_reminders() -> list[dict[str, str | int]]:
    """Fetch all reminders that have not been sent yet."""
    initialize_reminders_table()

    try:
        with get_database_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, title, due_time, status
                FROM reminders
                WHERE status = ?
                ORDER BY due_time ASC
                """,
                ("pending",),
            ).fetchall()
    except sqlite3.Error as exc:
        raise ReminderAgentError(f"Failed to fetch pending reminders: {exc}") from exc

    return [_row_to_dict(row) for row in rows]


def fetch_due_reminders(now: str | None = None) -> list[dict[str, str | int]]:
    """Fetch pending reminders whose due time has passed."""
    initialize_reminders_table()
    now = now or datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        with get_database_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, title, due_time, status
                FROM reminders
                WHERE status = ?
                  AND due_time <= ?
                ORDER BY due_time ASC
                """,
                ("pending", now),
            ).fetchall()
    except sqlite3.Error as exc:
        raise ReminderAgentError(f"Failed to fetch due reminders: {exc}") from exc

    return [_row_to_dict(row) for row in rows]


def update_reminder_status(reminder_id: int, status: str) -> None:
    """Update one reminder's status."""
    initialize_reminders_table()

    try:
        with get_database_connection() as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = ?
                WHERE id = ?
                """,
                (status, reminder_id),
            )
    except sqlite3.Error as exc:
        raise ReminderAgentError(f"Failed to update reminder status: {exc}") from exc
