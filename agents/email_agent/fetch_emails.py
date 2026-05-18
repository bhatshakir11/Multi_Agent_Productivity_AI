"""Gmail fetching utilities for the Email Agent.

This module owns Gmail OAuth and message parsing. It intentionally returns
plain dictionaries so future agents, schedulers, or a database layer can reuse
the email data without depending on Google API objects.
"""

from __future__ import annotations

import base64
import os
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# email_agent/fetch_emails.py -> email_agent -> agents -> productivity_ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "token.json"


class GmailAgentError(RuntimeError):
    """Raised when Gmail authentication or fetching fails."""


def _get_header(headers: list[dict[str, str]], name: str, default: str = "") -> str:
    """Return a Gmail header value using case-insensitive matching."""
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", default)
    return default


def _decode_body_data(data: str) -> str:
    """Decode Gmail's URL-safe base64 message body content."""
    if not data:
        return ""

    try:
        decoded_bytes = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        return decoded_bytes.decode("utf-8", errors="replace").strip()
    except (ValueError, UnicodeDecodeError):
        return ""


def _extract_plain_text(payload: dict[str, Any]) -> str:
    """Extract readable text from a Gmail MIME payload.

    Gmail messages may be single-part or multi-part. The agent prefers
    text/plain, but falls back to text/html stripped only by Gmail snippet later
    if no plain text is available.
    """
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return _decode_body_data(body_data)

    parts = payload.get("parts", [])
    plain_chunks: list[str] = []
    fallback_chunks: list[str] = []

    for part in parts:
        part_mime = part.get("mimeType", "")

        # Nested multipart messages are common when an email has attachments.
        if part_mime.startswith("multipart/"):
            nested_text = _extract_plain_text(part)
            if nested_text:
                plain_chunks.append(nested_text)
            continue

        decoded = _decode_body_data(part.get("body", {}).get("data", ""))
        if not decoded:
            continue

        if part_mime == "text/plain":
            plain_chunks.append(decoded)
        elif part_mime == "text/html":
            fallback_chunks.append(decoded)

    if plain_chunks:
        return "\n\n".join(plain_chunks).strip()

    return "\n\n".join(fallback_chunks).strip()


def _normalize_date(raw_date: str) -> str:
    """Convert an email Date header into ISO format when possible."""
    if not raw_date:
        return ""

    try:
        return parsedate_to_datetime(raw_date).isoformat()
    except (TypeError, ValueError, IndexError):
        return raw_date


def authenticate_gmail(
    credentials_path: Path | str = DEFAULT_CREDENTIALS_PATH,
    token_path: Path | str = DEFAULT_TOKEN_PATH,
):
    """Authenticate with Gmail and return a Gmail API service client.

    The first run opens a browser OAuth flow using credentials.json. Later runs
    reuse token.json and refresh it automatically when Google marks it expired.
    """
    credentials_path = Path(credentials_path)
    token_path = Path(token_path)
    creds: Credentials | None = None

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except ValueError as exc:
            raise GmailAgentError(f"Invalid token file: {token_path}") from exc

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise GmailAgentError(
                        f"Missing Gmail OAuth client file: {credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path),
                    SCOPES,
                )
                creds = flow.run_local_server(port=0)
        except RefreshError as exc:
            raise GmailAgentError(
                "Gmail token refresh failed. Delete token.json and authenticate again."
            ) from exc

        token_path.write_text(creds.to_json(), encoding="utf-8")

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as exc:
        raise GmailAgentError("Failed to create Gmail API client.") from exc


def parse_gmail_message(message: dict[str, Any]) -> dict[str, str]:
    """Convert a raw Gmail message resource into the agent's email schema."""
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    raw_date = _get_header(headers, "Date")
    body = _extract_plain_text(payload)
    snippet = message.get("snippet", "")

    return {
        "id": message.get("id", ""),
        "thread_id": message.get("threadId", ""),
        "sender": _get_header(headers, "From", "Unknown sender"),
        "subject": _get_header(headers, "Subject", "(No subject)"),
        "date": _normalize_date(raw_date),
        "snippet": snippet,
        "body": body or snippet,
    }


def fetch_latest_emails(max_results: int | None = None) -> list[dict[str, str]]:
    """Fetch recent Gmail messages as structured dictionaries."""
    max_results = max_results or int(os.getenv("EMAIL_AGENT_MAX_RESULTS", "5"))

    try:
        service = authenticate_gmail()
        response = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, labelIds=["INBOX"])
            .execute()
        )
        messages = response.get("messages", [])

        emails: list[dict[str, str]] = []
        for message_ref in messages:
            message = (
                service.users()
                .messages()
                .get(userId="me", id=message_ref["id"], format="full")
                .execute()
            )
            emails.append(parse_gmail_message(message))

        return emails
    except HttpError as exc:
        raise GmailAgentError(f"Gmail API request failed: {exc}") from exc
    except GmailAgentError:
        raise
    except Exception as exc:
        raise GmailAgentError(f"Unexpected Gmail fetch failure: {exc}") from exc
