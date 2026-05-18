"""Shared workflow context for multi-agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SharedContext:
    """Temporary state container passed across coordinated agent workflows."""

    workflow_name: str
    input_text: str = ""
    intent: str = "unknown"
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def set(self, key: str, value: Any) -> None:
        """Store workflow data."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Read workflow data."""
        return self.data.get(key, default)

    def add_error(self, message: str) -> None:
        """Record a non-fatal workflow error."""
        self.errors.append(message)

    def as_dict(self) -> dict[str, Any]:
        """Return serializable context state for debugging or persistence."""
        return {
            "workflow_name": self.workflow_name,
            "input_text": self.input_text,
            "intent": self.intent,
            "data": self.data,
            "errors": self.errors,
            "created_at": self.created_at,
        }
