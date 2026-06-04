import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
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
        /* Expand calendar grid cells for better visibility */
        .fc .fc-daygrid-day-frame {
            min-height: 150px !important;
        }
        .fc .fc-col-header-cell-cushion {
            font-size: 16px !important;
            padding: 10px 0 !important;
        }
        .fc-event, .fc-event-main, .fc-event-title, .fc-daygrid-event {
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow: visible !important;
            height: auto !important;
            font-size: 14px !important;
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

# Constants
DB_FILE, NOTES_FILE, EOD_FILE, ARCHIVE_FILE = "tasks_db.csv", "calendar_notes.csv", "eod_temp_logs.csv", "eod_master_archive.csv"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

# Helper Functions
def adjust_for_weekend(due_date):
    if due_date.weekday() == 5: return due_date + timedelta(days=2) # Sat -> Mon
    if due_date.weekday() == 6: return due_date + timedelta(days=1) # Sun -> Mon
    return due_date

def get_days_interval(freq):
    return 1 if freq == "Daily" else (7 if freq == "Weekly" else 30)

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except: return datetime.now().date()

# Initialization
if not os.path.exists(DB_FILE):
    df = pd.DataFrame({"task_id": [1], "task_name": ["New Task"], "frequency": ["Daily"], "last_completed": [datetime.now().strftime(STORAGE_DATE_FORMAT)], "task_priority": [3]})
    df.to_csv(DB_FILE, index=False)
else: df = pd.read_csv(DB_FILE)

# --- MONTHLY OVERVIEW ---
st.header("📅 Monthly Overview")
calendar_events = []
for _, row in df.iterrows():
    base_date = parse_date_safely(row.get('last_completed', datetime.now().strftime(STORAGE_DATE_FORMAT)))
    raw_due = base_date + timedelta(days=get_days_interval(row.get('frequency', 'Daily')))
    next_due = adjust_for_weekend(raw_due)
    
    calendar_events.append({
        "title": row.get('task_name', 'Task'),
        "start": next_due.strftime(STORAGE_DATE_FORMAT),
        "backgroundColor": "#1E3A8A",
        "allDay": True
    })

# Calendar Options defined BEFORE calling component
calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    "height": "auto",
    "dayMaxEvents": True,
    "dayHeaderFormat": {"weekday": "long"}, # Full day names (Sunday)
    "fixedWeekCount": False
}

calendar(events=calendar_events, options=calendar_options, key="main_cal")
