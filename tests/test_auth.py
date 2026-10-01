from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from google.auth.exceptions import RefreshError
from agents.calendar_agent.create_event import authenticate_calendar, CalendarAgentError
from agents.email_agent.fetch_emails import authenticate_gmail, GmailAgentError


@patch("agents.calendar_agent.create_event.Credentials")
@patch("agents.calendar_agent.create_event.InstalledAppFlow")
@patch("agents.calendar_agent.create_event.build")
def test_authenticate_calendar_refresh_error(mock_build, mock_flow_cls, mock_creds_cls, tmp_path: Path):
    """Test that Calendar auth deletes invalid token file and initiates OAuth flow on RefreshError."""
    token_file = tmp_path / "calendar_token.json"
    token_file.write_text("{}", encoding="utf-8")

    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("{}", encoding="utf-8")

    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "dummy_refresh_token"
    mock_creds.refresh.side_effect = RefreshError("invalid_grant")
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds

    mock_flow_instance = MagicMock()
    new_creds = MagicMock()
    new_creds.to_json.return_value = '{"token": "new_token"}'
    mock_flow_instance.run_local_server.return_value = new_creds
    mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance

    mock_service = MagicMock()
    mock_build.return_value = mock_service

    service = authenticate_calendar(credentials_path=creds_file, token_path=token_file)

    assert service == mock_service
    mock_flow_cls.from_client_secrets_file.assert_called_once_with(str(creds_file), ["https://www.googleapis.com/auth/calendar"])
    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8") == '{"token": "new_token"}'


@patch("agents.email_agent.fetch_emails.Credentials")
@patch("agents.email_agent.fetch_emails.InstalledAppFlow")
@patch("agents.email_agent.fetch_emails.build")
def test_authenticate_gmail_refresh_error(mock_build, mock_flow_cls, mock_creds_cls, tmp_path: Path):
    """Test that Gmail auth deletes invalid token file and initiates OAuth flow on RefreshError."""
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")

    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("{}", encoding="utf-8")

    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "dummy_refresh_token"
    mock_creds.refresh.side_effect = RefreshError("invalid_grant")
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds

    mock_flow_instance = MagicMock()
    new_creds = MagicMock()
    new_creds.to_json.return_value = '{"token": "new_token"}'
    mock_flow_instance.run_local_server.return_value = new_creds
    mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance

    mock_service = MagicMock()
    mock_build.return_value = mock_service

    service = authenticate_gmail(credentials_path=creds_file, token_path=token_file)

    assert service == mock_service
    mock_flow_cls.from_client_secrets_file.assert_called_once_with(str(creds_file), ["https://www.googleapis.com/auth/gmail.readonly"])
    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8") == '{"token": "new_token"}'
