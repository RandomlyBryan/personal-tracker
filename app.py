import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
import base64
import requests
from streamlit_calendar import calendar
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Personal Task Tracker", layout="wide")

# CUSTOM CSS: SLEEK DARK MODE + EXPANDED CALENDAR GRID
st.markdown(
    """
    <style>
        /* Expand calendar grid cells */
        .fc .fc-daygrid-day-frame { min-height: 150px !important; }
        .fc .fc-col-header-cell-cushion { font-size: 16px !important; padding: 10px 0 !important; }
        .fc-event, .fc-event-main, .fc-event-title, .fc-daygrid-event {
            white-space: normal !important; word-wrap: break-word !important;
            overflow: visible !important; height: auto !important; font-size: 14px !important;
        }
        [data-testid="stAppViewContainer"] { background-color: #0F1115 !important; }
        h1, h2, h3, h4 { color: #E2E8F0 !important; }
        .stTabs [data-baseweb="tab-list"] { background-color: #161920 !important; }
        .stTabs [data-baseweb="tab"] { background-color: #1A1F29 !important; color: #94A3B8 !important; }
        .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: #38BDF8 !important; }
        .stars-container { color: #F59E0B !important; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# Constants & Setup
DB_FILE, NOTES_FILE, EOD_FILE, PRIORITIES_FILE, ARCHIVE_FILE = "tasks_db.csv", "calendar_notes.csv", "eod_temp_logs.csv", "next_day_priorities.csv", "eod_master_archive.csv"
STORAGE_DATE_FORMAT = "%Y-%m-%d"
STAR_OPTIONS = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]

# Helper Functions
def adjust_for_weekend(due_date):
    if due_date.weekday() == 5: return due_date + timedelta(days=2) # Saturday -> Monday
    if due_date.weekday() == 6: return due_date + timedelta(days=1) # Sunday -> Monday
    return due_date

def get_days_interval(freq):
    return 1 if freq == "Daily" else (7 if freq == "Weekly" else 30)

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except: return datetime.now().date()

def push_to_github(filename):
    try:
        cfg = st.secrets["github"]
        token, repo, branch = cfg["token"], cfg["repo"], cfg["branch"]
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, params={"ref": branch})
        sha = res.json().get("sha") if res.status_code == 200 else None
        with open(filename, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        payload = {"message": f"Sync: {filename}", "content": encoded, "branch": branch}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except: pass

def save_and_push(df, filename):
    df.to_csv(filename, index=False)
    push_to_github(filename)

# Load Data
if not os.path.exists(DB_FILE):
    df = pd.DataFrame({"task_id": [1], "task_name": ["Example Task"], "task_description": ["Do this"], "frequency": ["Daily"], "is_recurring": ["Yes"], "last_completed": [datetime.now().strftime(STORAGE_DATE_FORMAT)], "task_priority": [3]})
    df.to_csv(DB_FILE, index=False)
else: df = pd.read_csv(DB_FILE)
if not os.path.exists(EOD_FILE) or os.path.getsize(EOD_FILE) == 0: eod_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"])
else: eod_df = pd.read_csv(EOD_FILE)
if not os.path.exists(ARCHIVE_FILE) or os.path.getsize(ARCHIVE_FILE) == 0: archive_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"])
else: archive_df = pd.read_csv(ARCHIVE_FILE)

# UI Layout
today = datetime.now().date()
st.header("📅 Monthly Overview")

calendar_events = []
for _, row in df.iterrows():
    base_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
    next_due = adjust_for_weekend(base_date + timedelta(days=get_days_interval(row.get('frequency', 'Daily'))))
    is_overdue = today >= next_due
    calendar_events.append({
        "title": row['task_name'],
        "start": next_due.strftime(STORAGE_DATE_FORMAT),
        "backgroundColor": "#EF4444" if is_overdue else "#1E3A8A",
        "allDay": True
    })

calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    "height": "auto",
    "dayMaxEvents": True,
    "dayHeaderFormat": {"weekday": "long"},
    "fixedWeekCount": False
}

calendar(events=calendar_events, options=calendar_options, key="main_cal")

# Tabs for other functionality
tabs = st.tabs(["🚨 Pending Tasks", "➕ New Task", "⚙️ Manage", "📝 EOD Report", "📊 History"])
# ... [Insert your existing tab logic for these sections here] ...
