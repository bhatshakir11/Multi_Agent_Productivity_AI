from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from utils.ai_client import ask_ai, AIClientError


@patch("utils.ai_client.get_ai_client")
def test_ask_ai_successful(mock_get_ai_client):
    """Test that ask_ai formats calls to the OpenAI client correctly and returns content."""
    mock_client = MagicMock()
    mock_get_ai_client.return_value = mock_client
    
    # Mock completion return object
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="Hello user"))]
    mock_client.chat.completions.create.return_value = mock_completion
    
    response = ask_ai("hi")
    assert response == "Hello user"
    
    # Assert parameters passed
    mock_client.chat.completions.create.assert_called_once()
    called_kwargs = mock_client.chat.completions.create.call_args[1]
    assert called_kwargs["messages"][1]["content"] == "hi"
    assert "response_format" not in called_kwargs


@patch("utils.ai_client.get_ai_client")
def test_ask_ai_with_response_format(mock_get_ai_client):
    """Test that ask_ai propagates response_format correctly."""
    mock_client = MagicMock()
    mock_get_ai_client.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content='{"title": "Sync"}'))]
    mock_client.chat.completions.create.return_value = mock_completion
    
    fmt = {"type": "json_object"}
    response = ask_ai("get json", response_format=fmt)
    
    assert response == '{"title": "Sync"}'
    called_kwargs = mock_client.chat.completions.create.call_args[1]
    assert called_kwargs["response_format"] == fmt


def test_ask_ai_empty_prompt():
    """Verify that calling ask_ai with empty prompt throws AIClientError."""
    with pytest.raises(AIClientError, match="prompt cannot be empty"):
        ask_ai("")
