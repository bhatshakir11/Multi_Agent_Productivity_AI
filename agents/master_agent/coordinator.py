"""Master Coordinator Agent entry point."""

from __future__ import annotations

import argparse
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler

from utils.logger import logger

from agents.master_agent.intent_router import route_intent
from agents.master_agent.shared_context import SharedContext
from agents.master_agent.workflow_engine import (
    DAILY_SUMMARY_WORKFLOW,
    EMAIL_TO_CALENDAR_REMINDER_WORKFLOW,
    REMINDER_CHECK_WORKFLOW,
    run_daily_summary_workflow,
    run_email_to_calendar_reminder_workflow,
    run_reminder_check_workflow,
)


try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def _print_context(context: SharedContext) -> None:
    """Print a compact workflow result."""
    print("\n================================")
    print("MASTER WORKFLOW RESULT")
    print("\nWorkflow:")
    print(context.workflow_name)
    print("\nIntent:")
    print(context.intent)

    if context.errors:
        print("\nErrors:")
        for error in context.errors:
            print(f"- {error}")

    notification_results = context.get("notification_results")
    if notification_results:
        print("\nNotifications:")
        for channel, result in notification_results.items():
            print(f"- {channel}: {result}")

    daily_summary = context.get("daily_summary")
    if daily_summary:
        print("\nSummary:")
        print(daily_summary)

    print("================================")


def run_master_workflow(text: str | None = None) -> SharedContext:
    """Run the Master Agent workflow selected by intent routing."""
    route = route_intent(text or "")
    workflow = str(route["workflow"])

    if workflow == EMAIL_TO_CALENDAR_REMINDER_WORKFLOW:
        context = run_email_to_calendar_reminder_workflow(text or "")
    elif workflow == DAILY_SUMMARY_WORKFLOW:
        context = run_daily_summary_workflow()
    elif workflow == REMINDER_CHECK_WORKFLOW:
        context = run_reminder_check_workflow()
    else:
        context = run_daily_summary_workflow()

    _print_context(context)
    return context


def run_master_daily_summary() -> SharedContext:
    """Public helper for scheduler jobs."""
    return run_daily_summary_workflow()


def run_master_reminder_check() -> SharedContext:
    """Public helper for scheduled due-reminder checks."""
    return run_reminder_check_workflow()


def start_master_scheduler(
    *,
    daily_hour: int = 8,
    daily_minute: int = 0,
    reminder_interval_minutes: int = 1,
) -> BackgroundScheduler:
    """Start recurring Master Agent orchestration jobs."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_master_daily_summary,
        "cron",
        hour=daily_hour,
        minute=daily_minute,
        id="master_daily_summary",
        replace_existing=True,
    )
    scheduler.add_job(
        run_master_reminder_check,
        "interval",
        minutes=reminder_interval_minutes,
        id="master_reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Master scheduler started. "
        f"Daily summary at {daily_hour:02d}:{daily_minute:02d}; "
        f"reminder checks every {reminder_interval_minutes} minute(s)."
    )
    return scheduler


def run_master_scheduler_forever() -> None:
    """Run scheduled Master Agent workflows until interrupted."""
    scheduler = start_master_scheduler()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Master scheduler stopped.")


def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the Master Agent CLI parser."""
    parser = argparse.ArgumentParser(description="Run the Master Coordinator Agent.")
    parser.add_argument(
        "text",
        nargs="*",
        help="Incoming request/event text to route, e.g. Meeting tomorrow at 4 PM",
    )
    parser.add_argument(
        "--daily-summary",
        action="store_true",
        help="Run the daily productivity summary workflow.",
    )
    parser.add_argument(
        "--check-reminders",
        action="store_true",
        help="Run the due-reminder workflow once.",
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start scheduled Master Agent workflows.",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.scheduler:
        run_master_scheduler_forever()
        return

    if args.check_reminders:
        context = run_reminder_check_workflow()
        _print_context(context)
        return

    if args.daily_summary:
        context = run_daily_summary_workflow()
        _print_context(context)
        return

    text = " ".join(args.text).strip()
    run_master_workflow(text or None)


if __name__ == "__main__":
    main()
