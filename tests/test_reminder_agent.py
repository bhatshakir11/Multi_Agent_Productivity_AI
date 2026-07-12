from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch
import pytest

from agents.reminder_agent.create_reminder import create_reminder
from agents.reminder_agent.fetch_reminders import (
    fetch_pending_reminders,
    fetch_due_reminders,
    update_reminder_status,
)


@pytest.fixture(autouse=True)
def mock_database_path(tmp_path):
    """Isolate tests using a temporary SQLite database file for each test case."""
    test_db = tmp_path / "test_app.db"
    with patch("agents.reminder_agent.create_reminder.DATABASE_PATH", test_db):
        # Trigger initialization to start with clean schemas
        yield test_db


def test_create_and_fetch_reminders():
    """Verify that reminders can be created and fetched from the database."""
    # Start with empty database
    pending = fetch_pending_reminders()
    assert len(pending) == 0
    
    # Create a reminder
    due_time = "2026-06-11 18:00"
    reminder = create_reminder("Solve DSA problems", due_time)
    assert reminder["title"] == "Solve DSA problems"
    assert reminder["due_time"] == due_time
    assert reminder["status"] == "pending"
    
    # Retrieve pending reminders and verify list matches
    pending = fetch_pending_reminders()
    assert len(pending) == 1
    assert pending[0]["title"] == "Solve DSA problems"
    assert pending[0]["id"] == reminder["id"]


def test_fetch_due_reminders():
    """Verify that only due reminders are retrieved based on checking timestamps."""
    now = datetime.now()
    past_time = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M")
    future_time = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M")
    
    # Create one past reminder and one future reminder
    create_reminder("Task past due", past_time)
    create_reminder("Task in future", future_time)
    
    # Check due reminders as of now
    now_str = now.strftime("%Y-%m-%d %H:%M")
    due = fetch_due_reminders(now=now_str)
    assert len(due) == 1
    assert due[0]["title"] == "Task past due"


def test_update_reminder_status():
    """Verify that updating a reminder status excludes it from pending fetches."""
    reminder = create_reminder("Testing task status", "2026-06-11 19:00")
    
    # Initial status is pending
    pending = fetch_pending_reminders()
    assert len(pending) == 1
    
    # Update to completed
    update_reminder_status(int(reminder["id"]), "completed")
    
    # Verify no longer shows up in pending
    pending = fetch_pending_reminders()
    assert len(pending) == 0
