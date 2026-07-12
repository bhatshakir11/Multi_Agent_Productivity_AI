"""AI event parsing for the Calendar Agent."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agents.calendar_agent.create_event import DEFAULT_TIME_ZONE, CalendarAgentError
from utils.ai_client import AIClientError, ask_ai


def _strip_json_fences(text: str) -> str:
    """Remove common markdown fences around model JSON."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    return cleaned


def _default_end_time(start_time: str, *, time_zone: str) -> str:
    """Return a one-hour default end time when AI omits it."""
    tz = ZoneInfo(time_zone)
    start = datetime.fromisoformat(start_time)

    if start.tzinfo is None:
        start = start.replace(tzinfo=tz)

    return (start + timedelta(hours=1)).isoformat()


def parse_event_from_text(
    text: str,
    *,
    time_zone: str = DEFAULT_TIME_ZONE,
) -> dict[str, str]:
    """Parse a natural-language event request into structured event data."""
    if not text or not text.strip():
        raise CalendarAgentError("Event text cannot be empty.")

    now = datetime.now(ZoneInfo(time_zone)).isoformat()
    prompt = f"""
Parse the user's text into one calendar event.

Current datetime: {now}
Timezone: {time_zone}

Return valid JSON only with these exact keys:
title, start_time, end_time, description, priority

Rules:
- start_time and end_time must be ISO 8601 datetimes.
- If no end time is given, make the event 1 hour long.
- priority must be Low, Medium, or High.
- description should be short and useful.
- Do not include markdown or commentary.

Text:
{text}
"""

    try:
        response = ask_ai(
            prompt,
            max_tokens=260,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = json.loads(_strip_json_fences(response))
    except (AIClientError, json.JSONDecodeError) as exc:
        raise CalendarAgentError(f"AI event parsing failed: {exc}") from exc

    title = str(parsed.get("title") or "Untitled Event").strip()
    start_time = str(parsed.get("start_time") or "").strip()
    end_time = str(parsed.get("end_time") or "").strip()

    if not start_time:
        raise CalendarAgentError("AI parser did not return start_time.")

    if not end_time:
        end_time = _default_end_time(start_time, time_zone=time_zone)

    return {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "description": str(parsed.get("description") or "").strip(),
        "priority": str(parsed.get("priority") or "Medium").strip(),
    }
