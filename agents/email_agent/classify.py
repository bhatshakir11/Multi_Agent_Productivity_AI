"""Email classification utilities."""

from __future__ import annotations

from agents.email_agent.summarize import ask_nvidia


ALLOWED_CATEGORIES = {"Important", "College", "Work", "Promotion", "Spam"}


def _normalize_category(raw_category: str) -> str:
    """Map model output back to one supported category."""
    cleaned = raw_category.strip().replace(".", "")

    for category in ALLOWED_CATEGORIES:
        if category.lower() in cleaned.lower():
            return category

    # Default to Important when the model is uncertain, so actionable messages
    # are less likely to be hidden by future notification or reminder agents.
    return "Important"


def classify_email(text: str) -> str:
    """Classify an email into one productivity category."""
    if not text or not text.strip():
        return "Important"

    prompt = f"""
Classify the email into exactly one category from this list:
Important
College
Work
Promotion
Spam

Category rules:
- Important: banking, UPI/payment, OTP/security, account alerts, bills, receipts,
  deadlines, interviews, official notices, or anything requiring attention.
- College: classes, assignments, exams, college events, faculty, campus notices.
- Work: jobs, interviews, office, clients, projects, HR, salary, professional tasks.
- Promotion: marketing, offers, sales, newsletters, product announcements.
- Spam: scams, phishing, suspicious links, fake prizes, irrelevant junk.
- Financial transaction alerts are Important, never Spam.

Return only the category name. No explanation.

Email:
{text[:6000]}
"""
    raw_category = ask_nvidia(prompt, max_tokens=20, temperature=0.0)
    return _normalize_category(raw_category)
