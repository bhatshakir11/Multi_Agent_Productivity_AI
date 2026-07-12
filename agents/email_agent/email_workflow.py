"""End-to-end workflow for the Email Agent.

Run from the productivity_ai directory:
    python -m agents.email_agent.email_workflow
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from agents.email_agent.classify import classify_email
from agents.email_agent.fetch_emails import GmailAgentError, fetch_latest_emails
from agents.email_agent.summarize import NvidiaAgentError, ask_nvidia, summarize_email
from notifications.telegram import TelegramNotificationError, send_telegram_message


try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


ALLOWED_CATEGORIES = {"Important", "College", "Work", "Promotion", "Spam"}
SUMMARY_CATEGORIES = {"Important", "College", "Work", "Promotion"}
IMPORTANT_KEYWORDS = (
    "upi",
    "payment",
    "paid",
    "received",
    "debited",
    "credited",
    "transaction",
    "bank",
    "otp",
    "security",
    "shortlisted",
    "interview",
    "deadline",
    "assignment",
)


def _email_text(email: dict[str, str]) -> str:
    """Build the text block sent to the AI model."""
    return "\n".join(
        [
            f"From: {email.get('sender', '')}",
            f"Subject: {email.get('subject', '')}",
            f"Date: {email.get('date', '')}",
            "",
            email.get("body") or email.get("snippet", ""),
        ]
    ).strip()


def fallback_email_summary(email: dict[str, str]) -> str:
    """Create a clean local summary when the AI provider is slow/unavailable."""
    source_text = (
        email.get("snippet")
        or email.get("body")
        or email.get("subject")
        or "No readable email content available."
    )
    compact = " ".join(source_text.split())

    if len(compact) > 260:
        compact = compact[:257].rstrip() + "..."

    return compact


def normalize_category(category: str, email: dict[str, str]) -> str:
    """Keep model categories inside policy and protect important alerts."""
    combined_text = " ".join(
        [
            email.get("sender", ""),
            email.get("subject", ""),
            email.get("snippet", ""),
            email.get("body", ""),
        ]
    ).lower()

    if any(keyword in combined_text for keyword in IMPORTANT_KEYWORDS):
        return "Important"

    cleaned = category.strip().replace(".", "")
    for allowed_category in ALLOWED_CATEGORIES:
        if allowed_category.lower() == cleaned.lower():
            return allowed_category

    return "Important"


def _json_from_model_response(response: str) -> dict[str, str]:
    """Parse model JSON while tolerating occasional markdown fences."""
    cleaned = response.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"task": "None", "deadline": "None"}

    return {
        "task": str(parsed.get("task") or "None").strip(),
        "deadline": str(parsed.get("deadline") or "None").strip(),
    }


def extract_task_and_deadline(text: str) -> dict[str, str]:
    """Extract the most important task and deadline from an email."""
    if not text or not text.strip():
        return {"task": "None", "deadline": "None"}

    prompt = f"""
Extract one important task and its deadline from this email.

Rules:
- If there is no task, use "None".
- If there is no deadline, use "None".
- Return valid JSON only with these keys: task, deadline.
- Do not include markdown or commentary.

Email:
{text[:6000]}
"""
    response = ask_nvidia(prompt, max_tokens=140, temperature=0.1)
    return _json_from_model_response(response)


def analyze_email_with_ai(email: dict[str, str]) -> dict[str, str]:
    """Analyze one email with a single model call for faster workflows."""
    text = _email_text(email)
    prompt = f"""
Analyze this email for a productivity assistant.

Return valid JSON only with these exact keys:
category, summary, task, deadline

Rules:
- category must be exactly one of: Important, College, Work, Promotion, Spam.
- Important: banking, UPI/payment, OTP/security, account alerts, bills, receipts,
  deadlines, interviews, official notices, or anything requiring attention.
- College: classes, assignments, exams, college events, faculty, campus notices.
- Work: jobs, interviews, office, clients, projects, HR, salary, professional tasks.
- Promotion: marketing, offers, sales, newsletters, product announcements.
- Spam: scams, phishing, suspicious links, fake prizes, irrelevant junk.
- Financial transaction alerts are Important, never Spam.
- summary must be exactly 2 concise lines.
- task should be one clear task, or "None".
- deadline should be the stated deadline, or "None".
- Do not include markdown or commentary.

Email:
{text[:6000]}
"""
    response = ask_nvidia(prompt, max_tokens=260, temperature=0.1)

    try:
        parsed = json.loads(response.strip().strip("`"))
    except json.JSONDecodeError:
        return {
            "sender": email.get("sender", "Unknown sender"),
            "subject": email.get("subject", "(No subject)"),
            "date": email.get("date", ""),
            "category": normalize_category("Important", email),
            "summary": fallback_email_summary(email),
            "task": "None",
            "deadline": "None",
        }

    return {
        "sender": email.get("sender", "Unknown sender"),
        "subject": email.get("subject", "(No subject)"),
        "date": email.get("date", ""),
        "category": normalize_category(str(parsed.get("category") or "Important"), email),
        "summary": str(parsed.get("summary") or "No summary available.").strip(),
        "task": str(parsed.get("task") or "None").strip(),
        "deadline": str(parsed.get("deadline") or "None").strip(),
    }


def process_email(email: dict[str, str]) -> dict[str, str]:
    """Run summarization, classification, and extraction for one email."""
    text = _email_text(email)
    category = classify_email(text)
    summary = summarize_email(text)
    task_info = extract_task_and_deadline(text)

    return {
        "sender": email.get("sender", "Unknown sender"),
        "subject": email.get("subject", "(No subject)"),
        "date": email.get("date", ""),
        "category": category,
        "summary": summary,
        "task": task_info["task"],
        "deadline": task_info["deadline"],
    }


def _is_today_email(email: dict[str, str], *, time_zone: str = "Asia/Kolkata") -> bool:
    """Return whether an email was received today in the user's timezone."""
    raw_date = email.get("date", "")

    if not raw_date:
        return False

    try:
        email_date = datetime.fromisoformat(raw_date)
    except ValueError:
        return False

    user_tz = ZoneInfo(time_zone)
    return email_date.astimezone(user_tz).date() == datetime.now(user_tz).date()


def fetch_today_email_summaries(limit: int = 5) -> list[dict[str, str]]:
    """Fetch summarized, productivity-relevant emails received today.

    This function is intentionally reusable by the Master Agent. It keeps Gmail
    access, classification, and summarization inside the Email Agent boundary.
    """
    fetch_limit = max(limit * 3, limit)
    emails = fetch_latest_emails(max_results=fetch_limit)
    summaries: list[dict[str, str]] = []

    for email in emails:
        if not _is_today_email(email):
            continue

        try:
            result = analyze_email_with_ai(email)
        except NvidiaAgentError as exc:
            result = {
                "sender": email.get("sender", "Unknown sender"),
                "subject": email.get("subject", "(No subject)"),
                "date": email.get("date", ""),
                "category": normalize_category("Important", email),
                "summary": fallback_email_summary(email),
                "task": "None",
                "deadline": "None",
            }
            print(f"Email Agent AI warning: {exc}")

        if result["category"] not in SUMMARY_CATEGORIES:
            continue

        summaries.append(
            {
                "sender": result["sender"],
                "subject": result["subject"],
                "summary": result["summary"],
                "category": result["category"],
            }
        )

        if len(summaries) >= limit:
            break

    return summaries


def print_email_result(result: dict[str, str]) -> None:
    """Print one processed email using the requested structured format."""
    print("\n================================")
    print(f"FROM: {result['sender']}")
    print(f"\nSUBJECT: {result['subject']}")
    if result.get("date"):
        print(f"\nDATE: {result['date']}")
    print("\nCATEGORY:")
    print(result["category"])
    print("\nSUMMARY:")
    print(result["summary"])
    print("\nTASK:")
    print(result["task"])
    print("\nDEADLINE:")
    print(result["deadline"])
    print("\n================================")


def format_email_telegram_message(result: dict[str, str]) -> str:
    """Build the Telegram message for one processed email."""
    return f"""\U0001f4e7 EMAIL SUMMARY

FROM: {result['sender']}

SUBJECT:
{result['subject']}

CATEGORY:
{result['category']}

SUMMARY:
{result['summary']}"""


def notify_email_result(result: dict[str, str]) -> None:
    """Send one processed email summary to Telegram."""
    try:
        send_telegram_message(format_email_telegram_message(result))
        print("Email Agent Telegram sent.")
    except TelegramNotificationError as exc:
        print(f"Email Agent Telegram warning: {exc}")


def run_email_agent(max_results: int | None = None) -> list[dict[str, str]]:
    """Fetch, process, print, notify, and return latest email agent results."""
    max_results = max_results or int(os.getenv("EMAIL_AGENT_MAX_RESULTS", "5"))

    try:
        emails = fetch_latest_emails(max_results=max_results)
    except GmailAgentError as exc:
        print(f"Email Agent Gmail error: {exc}")
        return []

    if not emails:
        print("Email Agent: no recent inbox emails found.")
        return []

    processed_results: list[dict[str, str]] = []
    for email in emails:
        try:
            result = analyze_email_with_ai(email)
        except NvidiaAgentError as exc:
            result = {
                "sender": email.get("sender", "Unknown sender"),
                "subject": email.get("subject", "(No subject)"),
                "date": email.get("date", ""),
                "category": normalize_category("Important", email),
                "summary": fallback_email_summary(email),
                "task": "None",
                "deadline": "None",
            }
            print(f"Email Agent AI warning: {exc}")
        except Exception as exc:
            result = {
                "sender": email.get("sender", "Unknown sender"),
                "subject": email.get("subject", "(No subject)"),
                "date": email.get("date", ""),
                "category": normalize_category("Important", email),
                "summary": fallback_email_summary(email),
                "task": "None",
                "deadline": "None",
            }
            print(f"Email Agent processing warning: {exc}")

        processed_results.append(result)
        print_email_result(result)
        notify_email_result(result)

    return processed_results


if __name__ == "__main__":
    run_email_agent()
