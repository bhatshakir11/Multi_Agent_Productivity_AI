"""Root orchestrator for the modular productivity AI system."""

from __future__ import annotations

from agents.master_agent.coordinator import run_master_workflow


def main() -> None:
    """Run the global Master Agent orchestration entry point."""
    run_master_workflow()


if __name__ == "__main__":
    main()
