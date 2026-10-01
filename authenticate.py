"""Interactive Google OAuth Authentication CLI.

Run this script directly from your terminal to authenticate Google Calendar & Gmail:
    python authenticate.py
"""

import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, Exception):
    pass

from agents.calendar_agent.create_event import authenticate_calendar
from agents.email_agent.fetch_emails import authenticate_gmail

def main():
    print("=" * 60)
    print(" GOOGLE OAUTH AUTHENTICATION SETUP")
    print("=" * 60)

    print("\n[1/2] Authenticating Google Calendar...")
    try:
        service_cal = authenticate_calendar()
        print("[SUCCESS] Google Calendar successfully authenticated! Token saved to .secrets/calendar_token.json")
    except Exception as e:
        print(f"[ERROR] Google Calendar Authentication failed: {e}")

    print("\n[2/2] Authenticating Gmail...")
    try:
        service_gmail = authenticate_gmail()
        print("[SUCCESS] Gmail successfully authenticated! Token saved to .secrets/token.json")
    except Exception as e:
        print(f"[ERROR] Gmail Authentication failed: {e}")

    print("\n==========================================================")
    print("OAuth Setup Process Finished!")
    print("==========================================================\n")

if __name__ == "__main__":
    main()
