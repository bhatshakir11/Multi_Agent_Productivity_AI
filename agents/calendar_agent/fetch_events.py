"""Google Calendar event fetching utilities."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError

from agents.calendar_agent.create_event import (
    DEFAULT_TIME_ZONE,
    CalendarAgentError,
    authenticate_calendar,
)


def _event_to_dict(event: dict[str, Any]) -> dict[str, str]:
    """Normalize Google Calendar event data for agents."""
    start = event.get("start", {})
    end = event.get("end", {})

    return {
        "id": str(event.get("id", "")),
        "title": str(event.get("summary", "(No title)")),
        "start_time": str(start.get("dateTime") or start.get("date") or ""),
        "end_time": str(end.get("dateTime") or end.get("date") or ""),
        "description": str(event.get("description", "")),
        "html_link": str(event.get("htmlLink", "")),
    }


def fetch_upcoming_events(max_results: int = 10) -> list[dict[str, str]]:
    """Fetch upcoming events from the primary calendar."""
    now_utc = datetime.utcnow().isoformat() + "Z"

    try:
        service = authenticate_calendar()
        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now_utc,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return [_event_to_dict(event) for event in response.get("items", [])]
    except HttpError as exc:
        raise CalendarAgentError(f"Google Calendar API error: {exc}") from exc
    except CalendarAgentError:
        raise
    except Exception as exc:
        raise CalendarAgentError(f"Unexpected Calendar fetch failure: {exc}") from exc


def fetch_todays_agenda(
    *,
    time_zone: str = DEFAULT_TIME_ZONE,
    max_results: int = 20,
) -> list[dict[str, str]]:
    """Fetch today's events from the primary calendar."""
    tz = ZoneInfo(time_zone)
    today = datetime.now(tz).date()
    start_of_day = datetime.combine(today, time.min, tzinfo=tz).isoformat()
    end_of_day = datetime.combine(today + timedelta(days=1), time.min, tzinfo=tz).isoformat()

    try:
        service = authenticate_calendar()
        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return [_event_to_dict(event) for event in response.get("items", [])]
    except HttpError as exc:
        raise CalendarAgentError(f"Google Calendar API error: {exc}") from exc
    except CalendarAgentError:
        raise
    except Exception as exc:
        raise CalendarAgentError(f"Unexpected agenda fetch failure: {exc}") from exc


def fetch_events_for_date(
    target_date: date,
    *,
    time_zone: str = DEFAULT_TIME_ZONE,
    max_results: int = 20,
) -> list[dict[str, str]]:
    """Fetch events for one calendar date."""
    tz = ZoneInfo(time_zone)
    start_of_day = datetime.combine(target_date, time.min, tzinfo=tz).isoformat()
    end_of_day = datetime.combine(
        target_date + timedelta(days=1),
        time.min,
        tzinfo=tz,
    ).isoformat()

    try:
        service = authenticate_calendar()
        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return [_event_to_dict(event) for event in response.get("items", [])]
    except HttpError as exc:
        raise CalendarAgentError(f"Google Calendar API error: {exc}") from exc
    except CalendarAgentError:
        raise
    except Exception as exc:
        raise CalendarAgentError(f"Unexpected date agenda fetch failure: {exc}") from exc


def fetch_agenda_for_days(
    days: int = 2,
    *,
    time_zone: str = DEFAULT_TIME_ZONE,
    max_results_per_day: int = 20,
) -> dict[str, list[dict[str, str]]]:
    """Fetch agenda grouped by day, starting today."""
    if days < 1:
        raise CalendarAgentError("days must be at least 1.")

    tz = ZoneInfo(time_zone)
    today = datetime.now(tz).date()
    agenda: dict[str, list[dict[str, str]]] = {}

    for offset in range(days):
        target_date = today + timedelta(days=offset)
        agenda[target_date.isoformat()] = fetch_events_for_date(
            target_date,
            time_zone=time_zone,
            max_results=max_results_per_day,
        )

    return agenda
