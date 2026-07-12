"""Google Calendar event creation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/calendar"]

# calendar_agent/create_event.py -> calendar_agent -> agents -> productivity_ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / ".secrets" / "credentials.json"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / ".secrets" / "calendar_token.json"
DEFAULT_TIME_ZONE = "Asia/Kolkata"


class CalendarAgentError(RuntimeError):
    """Raised when Google Calendar operations fail."""


def authenticate_calendar(
    credentials_path: Path | str = DEFAULT_CREDENTIALS_PATH,
    token_path: Path | str = DEFAULT_TOKEN_PATH,
):
    """Authenticate with Google Calendar and return a service client.

    A separate calendar_token.json is used so Calendar OAuth does not overwrite
    the Gmail token used by the Email Agent.
    """
    credentials_path = Path(credentials_path)
    token_path = Path(token_path)
    creds: Credentials | None = None

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except ValueError as exc:
            raise CalendarAgentError(f"Invalid calendar token file: {token_path}") from exc

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise CalendarAgentError(
                        f"Missing Google OAuth client file: {credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path),
                    SCOPES,
                )
                creds = flow.run_local_server(port=0)
        except RefreshError as exc:
            raise CalendarAgentError(
                "Calendar token refresh failed. Delete calendar_token.json and retry."
            ) from exc

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as exc:
        raise CalendarAgentError("Failed to create Google Calendar client.") from exc


def _event_to_dict(event: dict[str, Any]) -> dict[str, str]:
    """Normalize a Google Calendar event response."""
    start = event.get("start", {})
    end = event.get("end", {})

    return {
        "id": str(event.get("id", "")),
        "title": str(event.get("summary", "")),
        "start_time": str(start.get("dateTime") or start.get("date") or ""),
        "end_time": str(end.get("dateTime") or end.get("date") or ""),
        "description": str(event.get("description", "")),
        "html_link": str(event.get("htmlLink", "")),
    }


def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    *,
    time_zone: str = DEFAULT_TIME_ZONE,
) -> dict[str, str]:
    """Create an event on the primary Google Calendar."""
    if not title or not title.strip():
        raise CalendarAgentError("Calendar event title cannot be empty.")

    if not start_time or not end_time:
        raise CalendarAgentError("Calendar event start_time and end_time are required.")

    event_body = {
        "summary": title.strip(),
        "description": description.strip(),
        "start": {"dateTime": start_time, "timeZone": time_zone},
        "end": {"dateTime": end_time, "timeZone": time_zone},
    }

    try:
        service = authenticate_calendar()
        created_event = (
            service.events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )
        return _event_to_dict(created_event)
    except HttpError as exc:
        raise CalendarAgentError(f"Google Calendar API error: {exc}") from exc
    except CalendarAgentError:
        raise
    except Exception as exc:
        raise CalendarAgentError(f"Unexpected Calendar create failure: {exc}") from exc
