from __future__ import annotations

from unittest.mock import patch
import pytest

from agents.master_agent.intent_router import route_intent, WORKFLOWS
from utils.ai_client import AIClientError


def test_keyword_routing_daily_summary():
    """Verify that daily summary keywords trigger DAILY_SUMMARY_WORKFLOW without LLM calls."""
    # We do not mock ask_ai because it shouldn't even be called for direct daily summary keywords
    with patch("agents.master_agent.intent_router.ask_ai") as mock_ask_ai:
        result = route_intent("productivity summary")
        assert result == WORKFLOWS["DAILY_SUMMARY_WORKFLOW"]
        mock_ask_ai.assert_not_called()


@patch("agents.master_agent.intent_router.ask_ai")
def test_llm_routing_success(mock_ask_ai):
    """Verify that a successful LLM classification routes to the correct workflow."""
    mock_ask_ai.return_value = "EMAIL_WORKFLOW"
    
    result = route_intent("Please check my university inbox")
    assert result == WORKFLOWS["EMAIL_WORKFLOW"]
    mock_ask_ai.assert_called_once()


@patch("agents.master_agent.intent_router.ask_ai")
def test_llm_routing_invalid_response_fallback(mock_ask_ai):
    """Verify that if the LLM returns an invalid category, it falls back to keyword matching."""
    mock_ask_ai.return_value = "INVALID_WORKFLOW_NAME"
    
    # "remind me to write tests" contains "remind", which keyword fallback should route to REMINDER_WORKFLOW
    result = route_intent("remind me to write tests")
    assert result == WORKFLOWS["REMINDER_WORKFLOW"]


@patch("agents.master_agent.intent_router.ask_ai")
def test_llm_routing_exception_fallback(mock_ask_ai):
    """Verify that if ask_ai raises an exception, the router falls back to keyword matching."""
    mock_ask_ai.side_effect = AIClientError("NVIDIA API Down")
    
    # "show me tech news" contains "news", which keyword fallback routes to NEWS_WORKFLOW
    result = route_intent("show me tech news")
    assert result == WORKFLOWS["NEWS_WORKFLOW"]
