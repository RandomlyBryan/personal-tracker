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

# CUSTOM CSS: SLEEK DARK MODE THEME ENGINE
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .main, h1, h2, h3, h4, h5, h6, p, label, .stTabs button {
            font-family: 'Georgia', serif !important;
        }
        input, textarea, select {
            font-family: 'Georgia', serif !important;
        }
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0F1115 !important;
        }
        h1, h2, h3, h4 {
            color: #E2E8F0 !important;
            text-shadow: 1px 1px 2px #000;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background-color: #161920 !important;
            padding: 6px;
            border-radius: 8px;
            border: 1px solid #232936;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #1A1F29 !important;
            color: #94A3B8 !important;
            border-radius: 5px;
            padding: 8px 16px;
            border: 1px solid transparent;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E3A8A !important;
            color: #38BDF8 !important;
            border: 1px solid #0284C7 !important;
            font-weight: bold !important;
        }
        .fc .fc-daygrid-event {
            white-space: normal !important;
            height: auto !important;
            word-wrap: break-word !important;
        }
        .fc-event-main, .fc-event-title {
            white-space: normal !important;
            overflow: visible !important;
        }
        .stars-container {
            color: #F59E0B !important;
            font-weight: bold;
            letter-spacing: 3px;
            margin-left: 6px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Constants & Setup
DB_FILE = "tasks_db.csv"
NOTES_FILE = "calendar_notes.csv"
EOD_FILE = "eod_temp_logs.csv"
PRIORITIES_FILE = "next_day_priorities.csv" 
ARCHIVE_FILE = "eod_master_archive.csv"
DATE_FORMAT = "%d/%m/%Y"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

STAR_OPTIONS = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]

# Initialization Session States
if "editing_task_id" not in st.session_state: st.session_state.editing_task_id = None
if "editing_note_id" not in st.session_state: st.session_state.editing_note_id = None

# Helper Functions
def push_to_github(filename):
    try:
        cfg = st.secrets["github"]
        token, repo, branch = cfg["token"], cfg["repo"], cfg["branch"]
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, params={"ref": branch})
        sha = res.json().get("sha") if res.status_code == 200 else None
        with open(filename, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode("utf-8")
        payload = {"message": f"🤖 Sync: {filename}", "content": encoded_content, "branch": branch}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception: pass

def adjust_for_weekend(due_date):
    if due_date.weekday() == 5: return due_date + timedelta(days=2) # Saturday -> Monday
    if due_date.weekday() == 6: return due_date + timedelta(days=1) # Sunday -> Monday
    return due_date

def get_days_interval(freq_string):
    return 1 if freq_string == "Daily" else (7 if freq_string == "Weekly" else 30)

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except: return datetime.now().date()

# Database Load/Verify
if not os.path.exists(DB_FILE):
    df = pd.DataFrame({"task_id": [1], "task_name": ["New Task"], "task_description": [""], "task_url": [""], "frequency": ["Daily"], "is_recurring": ["Yes"], "last_completed": [datetime.now().strftime(STORAGE_DATE_FORMAT)], "task_screenshot_b64": [""], "task_priority": [3]})
    df.to_csv(DB_FILE, index=False)
else: df = pd.read_csv(DB_FILE)

# (Add similar load/check blocks for EOD_FILE, ARCHIVE_FILE, NOTES_FILE, PRIORITIES_FILE)
# ... [Assuming standard boilerplate for these files] ...

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

# App UI Logic
main_col, _ = st.columns([12, 1])
with main_col:
    st.header("📅 Monthly Overview")
    calendar_events = []
    for _, row in df.iterrows():
        base_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
        raw_next_due = base_date + timedelta(days=get_days_interval(row.get('frequency', 'Daily')))
        next_due = adjust_for_weekend(raw_next_due)
        is_overdue = today >= next_due
        
        calendar_events.append({
            "title": f"⚠️ Due: {row['task_name']}" if is_overdue else row['task_name'],
            "start": next_due.strftime(STORAGE_DATE_FORMAT),
            "backgroundColor": "#EF4444" if is_overdue else "#1E3A8A",
            "allDay": True
        })
    
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "height": "auto",
        "dayMaxEvents": True
    }
    calendar(events=calendar_events, options=calendar_options, key="calendar_view")
