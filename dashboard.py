"""Streamlit Web Dashboard for the Multi-Agent Productivity AI.

Provides a unified interface for recruiters and users to view calendar events,
email summaries, SQLite reminders, tech news, and interact with the Master Agent.
"""

from __future__ import annotations

from datetime import datetime
import os
import streamlit as st

# Core imports from our agent workflows
from agents.master_agent.coordinator import run_master_workflow
from agents.calendar_agent.fetch_events import fetch_todays_agenda
from agents.email_agent.email_workflow import fetch_today_email_summaries
from agents.news_agent.fetch_news import fetch_top_tech_news
from agents.reminder_agent.fetch_reminders import (
    fetch_pending_reminders,
    update_reminder_status,
)
from agents.reminder_agent.create_reminder import create_reminder


# Configuration and page setup
st.set_page_config(
    page_title="Multi-Agent Productivity AI",
    page_icon="🚀",
    layout="wide",
)

# Custom CSS for rich aesthetics
st.markdown(
    """
    <style>
    .reportview-container {
        background: #0e1117;
    }
    .metric-card {
        background-color: #1f2937;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #374151;
        margin-bottom: 15px;
    }
    .email-badge {
        font-size: 0.8rem;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-important { background-color: #ef4444; color: white; }
    .badge-college { background-color: #3b82f6; color: white; }
    .badge-work { background-color: #10b981; color: white; }
    .badge-promotion { background-color: #f59e0b; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Title & Description
st.title("🚀 Multi-Agent Productivity AI Dashboard")
st.markdown(
    "Welcome to your centralized personal command center. This dashboard coordinates "
    "specialist agents managing your Calendar, Gmail Inbox, Reminders database, and Tech News feeds."
)

# Check for API Keys to decide whether to prompt the user for Demo Mode
missing_keys = []
if not os.getenv("NVIDIA_API_KEY") and not os.getenv("NVIDIA_NIM_API_KEY"):
    missing_keys.append("NVIDIA_API_KEY")
if not os.path.exists(".secrets/token.json"):
    missing_keys.append("Gmail OAuth token (token.json)")
if not os.path.exists(".secrets/calendar_token.json"):
    missing_keys.append("Google Calendar OAuth token (calendar_token.json)")

# Store Demo Mode setting in session state
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = len(missing_keys) > 0

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Agent Settings")
    
    # Toggle for Demo/Mock mode
    st.session_state.demo_mode = st.checkbox(
        "Enable Demo Mode (Mock Data)",
        value=st.session_state.demo_mode,
        help="Runs workflows with realistic mock data to demonstrate the dashboard features without API keys.",
    )
    
    if st.session_state.demo_mode:
        st.warning("⚠️ Running in Demo Mode with mock data.")
    elif missing_keys:
        st.info(f"💡 Missing credentials: {', '.join(missing_keys)}. We recommend using Demo Mode.")

    st.markdown("---")
    st.markdown("### 🤖 Agent Diagnostic logs")
    st.text_area(
        "System Log Output",
        value="[system] Master Agent online.\n[scheduler] Background trigger active.\n[db] SQLite connection initialized.",
        height=180,
        disabled=True,
    )
    
    st.markdown("---")
    st.markdown("Created by Bhat Shakir | Placement Showcase")


# Master Agent Chat Section & Quick Summary Action
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("💬 Chat with Master Agent")
    st.markdown("Ask the coordinator agent to schedule meetings, set reminders, or fetch technology digests.")
    
    # Session state to hold chat logs
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am your Master Coordinator. How can I help you today?"}
        ]

    # Render previous messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input box
    if user_prompt := st.chat_input("E.g., Schedule project review tomorrow at 3 PM"):
        # Display user input
        with st.chat_message("user"):
            st.write(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        
        # Call agent workflow
        with st.chat_message("assistant"):
            with st.spinner("Agent coordination in progress..."):
                if st.session_state.demo_mode:
                    # Realistic Mock Coordinator Responses
                    if "remind" in user_prompt.lower() or "due" in user_prompt.lower():
                        response_text = "⏰ **REMINDER WORKFLOW COMPLETE**\n\nCreated SQLite reminder:\n- Task: Finish homework\n- Due Time: Tomorrow at 5:00 PM\n\nTelegram notification dispatched successfully!"
                        # Add a reminder to SQLite database for rich demonstration
                        try:
                            create_reminder("Finish homework (Added via Chat)", datetime.now().strftime("%Y-%m-%d 17:00"))
                        except Exception:
                            pass
                    elif "meeting" in user_prompt.lower() or "schedule" in user_prompt.lower() or "tomorrow" in user_prompt.lower():
                        response_text = "📅 **MASTER AGENT WORKFLOW COMPLETE**\n\nGoogle Calendar Event:\n- Title: Project Review Sync\n- Start: Tomorrow at 3:00 PM\n- End: Tomorrow at 4:00 PM\n\nCreated SQLite Reminder:\n- Task: Upcoming event: Project Review Sync\n- Due Time: Tomorrow at 2:30 PM\n\nTelegram notification dispatched successfully!"
                    else:
                        response_text = f"🤖 Master Agent routed intent to fallback.\nProcessed input: '{user_prompt}'\nWorkflow run: `DAILY_SUMMARY_WORKFLOW`."
                else:
                    try:
                        context = run_master_workflow(user_prompt)
                        # Build output response from coordinator context
                        lines = [f"**Workflow**: `{context.workflow_name}`", ""]
                        if context.errors:
                            lines.append("❌ **Errors encountered**:")
                            for error in context.errors:
                                lines.append(f"- {error}")
                        else:
                            lines.append("✅ **Task completed successfully!**")
                        
                        daily_summary = context.get("daily_summary")
                        if daily_summary:
                            lines.append(f"\n{daily_summary}")
                        
                        reminder = context.get("reminder")
                        if reminder:
                            lines.append(f"\n⏰ Created Reminder: *{reminder['title']}* due at {reminder['due_time']}")
                            
                        event = context.get("calendar_event")
                        if event:
                            lines.append(f"\n📅 Scheduled Calendar Event: *{event['title']}* ({event['start_time']})")
                            
                        response_text = "\n".join(lines)
                    except Exception as e:
                        response_text = f"❌ Error running Master Agent: {e}"
                
                st.write(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

with col2:
    st.subheader("📊 Control Center Feeds")
    
    # Quick manual triggers
    trigger_col, status_col = st.columns([1, 2])
    with trigger_col:
        if st.button("🔄 Daily Summary Workflow", use_container_width=True):
            st.info("Executing Daily Summary...")
            if st.session_state.demo_mode:
                st.success("Daily summary notification dispatched via Telegram bot mock channel!")
            else:
                try:
                    run_master_workflow("daily summary")
                    st.success("Daily Summary ran successfully!")
                except Exception as e:
                    st.error(f"Execution failed: {e}")

    # Tabs for feeds
    tab_calendar, tab_emails, tab_reminders, tab_news = st.tabs(
        ["📅 Calendar", "📧 Emails", "⏰ Reminders", "📰 News"]
    )
    
    # 1. Calendar Tab
    with tab_calendar:
        st.markdown("#### Google Calendar Agenda (Today)")
        if st.session_state.demo_mode:
            mock_events = [
                {"title": "Placement Mock Interview Prep", "start_time": "2026-06-12T10:00:00+05:30", "description": "Prep session with batchmates"},
                {"title": "Sync with Project Mentor", "start_time": "2026-06-12T15:30:00+05:30", "description": "Reviewing system architecture"},
            ]
            for event in mock_events:
                st.markdown(
                    f"<div class='metric-card'><b>{event['title']}</b><br>"
                    f"⏰ {datetime.fromisoformat(event['start_time']).strftime('%I:%M %p')}<br>"
                    f"<small>{event['description']}</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            try:
                events = fetch_todays_agenda()
                if not events:
                    st.info("No events scheduled for today.")
                else:
                    for event in events:
                        start_raw = event.get('start_time', '')
                        start_str = "Any time"
                        if start_raw:
                            try:
                                start_str = datetime.fromisoformat(start_raw).strftime('%I:%M %p')
                            except ValueError:
                                start_str = start_raw
                                
                        st.markdown(
                            f"<div class='metric-card'><b>{event.get('title', 'Untitled')}</b><br>"
                            f"⏰ {start_str}<br>"
                            f"<small>{event.get('description', '')}</small></div>",
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                st.error(f"Failed to fetch calendar: {e}")
                st.info("💡 Set up Google Calendar OAuth2 credentials or enable Demo Mode in the sidebar.")
                
    # 2. Emails Tab
    with tab_emails:
        st.markdown("#### Gmail Categorized Alerts (Today)")
        if st.session_state.demo_mode:
            mock_emails = [
                {"sender": "placement@university.edu", "subject": "Shortlist Announcement: TechCorp Inc.", "summary": "You have been shortlisted for the final round interviews of TechCorp Inc.\nSchedule slot by 11 PM today.", "category": "Important"},
                {"sender": "professor_dbms@university.edu", "subject": "DBMS Assignment 3 Extension", "summary": "DBMS assignment submission date extended to Friday noon.\nEnsure proper normalization documents are uploaded.", "category": "College"},
                {"sender": "hiring@innovations.io", "subject": "Software Engineer Internship Offer Details", "summary": "Hiring manager wants to review initial CTC breakdown details.\nResponse requested by tomorrow morning.", "category": "Work"},
            ]
            for email in mock_emails:
                badge_class = f"badge-{email['category'].lower()}"
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<b>{email['subject']}</b> <span class='email-badge {badge_class}'>{email['category']}</span><br>"
                    f"<small>From: {email['sender']}</small><br>"
                    f"<p style='margin-top: 5px;'>{email['summary']}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            try:
                emails = fetch_today_email_summaries(limit=5)
                if not emails:
                    st.info("No important emails summarized today.")
                else:
                    for email in emails:
                        cat = email.get("category", "Important")
                        badge_class = f"badge-{cat.lower()}"
                        st.markdown(
                            f"<div class='metric-card'>"
                            f"<b>{email.get('subject', '(No Subject)')}</b> <span class='email-badge {badge_class}'>{cat}</span><br>"
                            f"<small>From: {email.get('sender', 'Unknown')}</small><br>"
                            f"<p style='margin-top: 5px;'>{email.get('summary', '')}</p>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                st.error(f"Failed to fetch emails: {e}")
                st.info("💡 Set up Google Gmail API credentials or enable Demo Mode in the sidebar.")

    # 3. Reminders Tab
    with tab_reminders:
        st.markdown("#### SQLite Pending Reminders")
        
        # Form to add reminder
        with st.form("add_reminder_form", clear_on_submit=True):
            r_col1, r_col2 = st.columns([2, 1])
            with r_col1:
                title_input = st.text_input("New Reminder Title", placeholder="Finish DSA problems")
            with r_col2:
                due_input = st.text_input("Due (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d 18:00"))
            
            submit_rem = st.form_submit_button("Add Reminder")
            if submit_rem:
                if title_input and due_input:
                    try:
                        create_reminder(title_input, due_input)
                        st.success(f"Added: '{title_input}'")
                    except Exception as e:
                        st.error(f"Database error: {e}")
                else:
                    st.warning("Please fill all fields")

        # Show pending reminders
        try:
            reminders = fetch_pending_reminders()
            if not reminders:
                st.info("No pending reminders.")
            else:
                for rem in reminders:
                    rem_col1, rem_col2 = st.columns([3, 1])
                    with rem_col1:
                        st.markdown(f"⏰ **{rem['title']}**<br><small>Due: {rem['due_time']}</small>", unsafe_allow_html=True)
                    with rem_col2:
                        if st.button("Mark Completed", key=f"rem_{rem['id']}"):
                            update_reminder_status(int(rem['id']), "completed")
                            st.success("Completed!")
                            st.rerun()
                    st.markdown("---")
        except Exception as e:
            st.error(f"Could not load reminders database: {e}")

    # 4. News Tab
    with tab_news:
        st.markdown("#### Technology News Digest")
        if st.session_state.demo_mode:
            mock_news = [
                {"title": "Open-Source Models Rival Proprietary Equivalents at Coding Tasks", "source": "TechCrunch", "url": "https://techcrunch.com"},
                {"title": "NVIDIA NIM Infrastructure Accelerates Agentic AI Orchestration Layers", "source": "VentureBeat", "url": "https://venturebeat.com"},
                {"title": "New Web Standards Propose Decentralized Browser State Storage", "source": "HackerNews", "url": "https://news.ycombinator.com"},
            ]
            for item in mock_news:
                st.markdown(
                    f"<div class='metric-card'>"
                    f"📰 <b><a href='{item['url']}' target='_blank'>{item['title']}</a></b><br>"
                    f"<small>Source: {item['source']}</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            try:
                news_items = fetch_top_tech_news(page_size=5)
                if not news_items:
                    st.info("No technology headlines fetched.")
                else:
                    for item in news_items:
                        st.markdown(
                            f"<div class='metric-card'>"
                            f"📰 <b><a href='{item.get('url', '#')}' target='_blank'>{item.get('title', 'No Title')}</a></b><br>"
                            f"<small>Source: {item.get('source', 'Unknown')}</small></div>",
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                st.error(f"Failed to fetch news: {e}")
