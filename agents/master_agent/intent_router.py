"""Intent routing for the Master Agent."""

from __future__ import annotations

from utils.ai_client import AIClientError, ask_ai


CALENDAR_KEYWORDS = (
    "meeting",
    "review",
    "class",
    "appointment",
    "event",
    "call",
    "schedule",
)
REMINDER_KEYWORDS = ("remind", "reminder", "due", "deadline", "submit", "finish")
NEWS_KEYWORDS = ("news", "headline", "technology", "tech")
EMAIL_KEYWORDS = ("email", "gmail", "inbox")
SUMMARY_KEYWORDS = ("daily summary", "productivity summary", "today summary")

WORKFLOWS: dict[str, dict[str, object]] = {
    "DAILY_SUMMARY_WORKFLOW": {
        "intent": "daily_summary",
        "workflow": "DAILY_SUMMARY_WORKFLOW",
        "agents": ["calendar_agent", "reminder_agent", "news_agent"],
    },
    "EMAIL_TO_CALENDAR_REMINDER_WORKFLOW": {
        "intent": "calendar_event_with_reminder",
        "workflow": "EMAIL_TO_CALENDAR_REMINDER_WORKFLOW",
        "agents": ["calendar_agent", "reminder_agent", "notifications"],
    },
    "REMINDER_WORKFLOW": {
        "intent": "reminder",
        "workflow": "REMINDER_WORKFLOW",
        "agents": ["reminder_agent", "notifications"],
    },
    "NEWS_WORKFLOW": {
        "intent": "news",
        "workflow": "NEWS_WORKFLOW",
        "agents": ["news_agent", "notifications"],
    },
    "EMAIL_WORKFLOW": {
        "intent": "email",
        "workflow": "EMAIL_WORKFLOW",
        "agents": ["email_agent", "notifications"],
    }
}


def _keyword_fallback_routing(normalized: str) -> dict[str, object]:
    """Pure keyword matching logic for fallback or fast routing."""
    has_calendar_signal = any(keyword in normalized for keyword in CALENDAR_KEYWORDS)
    has_reminder_signal = any(keyword in normalized for keyword in REMINDER_KEYWORDS)
    has_time_signal = any(
        keyword in normalized
        for keyword in ("today", "tomorrow", "am", "pm", "morning", "evening")
    )

    if has_calendar_signal and has_time_signal:
        return WORKFLOWS["EMAIL_TO_CALENDAR_REMINDER_WORKFLOW"]

    if has_reminder_signal:
        return WORKFLOWS["REMINDER_WORKFLOW"]

    if any(keyword in normalized for keyword in NEWS_KEYWORDS):
        return WORKFLOWS["NEWS_WORKFLOW"]

    if any(keyword in normalized for keyword in EMAIL_KEYWORDS):
        return WORKFLOWS["EMAIL_WORKFLOW"]

    return WORKFLOWS["DAILY_SUMMARY_WORKFLOW"]


def route_intent(text: str) -> dict[str, object]:
    """Analyze incoming text and decide which workflow should run."""
    normalized = text.lower().strip()

    if not normalized:
        return WORKFLOWS["DAILY_SUMMARY_WORKFLOW"]

    # High-speed exact summary keyword bypass
    if any(keyword in normalized for keyword in SUMMARY_KEYWORDS):
        return WORKFLOWS["DAILY_SUMMARY_WORKFLOW"]

    # Attempt dynamic LLM intent classification
    prompt = f"""
Analyze the user's incoming request and select the most appropriate workflow category.

Categories:
- DAILY_SUMMARY_WORKFLOW: General overview, productivity summary, tech news + events + emails together, greetings or hello.
- EMAIL_TO_CALENDAR_REMINDER_WORKFLOW: Scheduling a calendar event or appointment with specific date or time signals (e.g. meeting tomorrow at 4 PM, sync on Friday at 10 AM, class tomorrow).
- REMINDER_WORKFLOW: Setting a specific task deadline or simple reminder (e.g. remind me to finish report, due tomorrow, submit project).
- NEWS_WORKFLOW: Requesting news updates or technology news specifically (e.g. show me the tech news, technology headlines).
- EMAIL_WORKFLOW: Requesting to fetch, summarize, or check emails (e.g. fetch my inbox emails, summarize my college emails).

Choose exactly one category from the list above. Return ONLY the category name. Do not include markdown or explanations.

User Request:
"{text}"
"""

    try:
        response = ask_ai(
            prompt,
            system_prompt="You are a precise routing agent. Return only the selected category name.",
            temperature=0.0,
            max_tokens=40,
        )
        cleaned_response = response.strip().strip("`").strip()
        
        # Exact match check
        if cleaned_response in WORKFLOWS:
            return WORKFLOWS[cleaned_response]
            
        # Substring/Containment check
        for wf_name, wf_dict in WORKFLOWS.items():
            if wf_name in cleaned_response:
                return wf_dict
    except AIClientError:
        pass  # Fall back gracefully

    # Fallback to local keyword matcher
    return _keyword_fallback_routing(normalized)
