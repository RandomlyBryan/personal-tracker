import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
import base64
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Personal Task Tracker", layout="wide")

# CUSTOM CSS: SLEEK DARK MODE THEME ENGINE (MATTE CHARCOAL & ELECTRIC BLUE)
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
        [data-testid="stWidgetLabel"] p {
            color: #94A3B8 !important;
        }
        div[data-baseweb="input"], div[data-baseweb="textarea"], select, div[data-baseweb="select"] {
            background-color: #161920 !important;
            border: 1px solid #2D3748 !important;
            color: #F8FAFC !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
            border-color: #0284C7 !important;
            box-shadow: 0 0 4px #0284C7 !important;
        }
        div.clean-copy code {
            background-color: transparent !important;
            border: none !important;
            color: #38BDF8 !important;
            font-size: 1.1em !important;
            font-family: 'Georgia', serif !important;
        }
        div.clean-copy [data-testid="stCodeBlock"] {
            background-color: #161920 !important;
            border: 1px solid #2D3748 !important;
            border-radius: 6px;
            margin-bottom: 6px !important;
            padding: 2px 10px !important;
        }
        div.clean-report-block [data-testid="stCodeBlock"] {
            background-color: #090B0E !important;
            border: 1px solid #2D3748 !important;
            border-radius: 6px;
            padding: 8px 12px !important;
        }
        div.clean-report-block code {
            background-color: transparent !important;
            border: none !important;
            color: #38BDF8 !important;
            font-family: 'Georgia', serif !important;
            font-size: 1.1em !important;
            line-height: 1.5 !important;
            white-space: pre-wrap !important;
        }
        div.pending-row-form button {
            background-color: #0284C7 !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border: 1px solid #0369A1 !important;
            border-radius: 6px !important;
            width: 100% !important;
            transition: all 0.25s ease;
        }
        div.pending-row-form button:hover {
            background-color: #0ea5e9 !important;
            box-shadow: 0 0 8px #0ea5e9 !important;
        }
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background-color: transparent !important;
        }
        button[kind="secondary"] {
            background-color: #0284C7 !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border: 1px solid #0369A1 !important;
            border-radius: 6px !important;
            transition: all 0.25s ease;
        }
        button[kind="secondary"]:hover {
            background-color: #0ea5e9 !important;
            box-shadow: 0 0 8px #0ea5e9 !important;
            transform: scale(1.01);
        }
        a[role="button"] {
            background-color: #1E293B !important;
            color: #38BDF8 !important;
            border: 1px solid #334155 !important;
            font-family: 'Georgia', serif !important;
        }
        a[role="button"]:hover {
            background-color: #334155 !important;
            box-shadow: 0 0 8px #334155 !important;
        }
        div[data-testid="stNotification"] {
            background-color: #161920 !important;
            border-left: 5px solid #0284C7 !important;
            border-top: 1px solid #232936 !important;
            border-right: 1px solid #232936 !important;
            border-bottom: 1px solid #232936 !important;
        }
        div[data-testid="stNotification"] p, div[data-testid="stNotification"] b {
            color: #E2E8F0 !important;
        }
        div[data-testid="stExpander"] {
            background-color: #161920 !important;
            border: 1px solid #232936 !important;
        }
        div[data-testid="stMetricContainer"] {
            background-color: #161920 !important;
            border: 1px solid #232936 !important;
            border-radius: 6px;
            padding: 10px 14px !important;
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

if "editing_task_id" not in st.session_state: st.session_state.editing_task_id = None
if "editing_note_id" not in st.session_state: st.session_state.editing_note_id = None
if "emails_sent_today" not in st.session_state: st.session_state.emails_sent_today = []

def push_to_github(filename):
    try:
        cfg = st.secrets["github"]
        token = cfg["token"]
        repo = cfg["repo"]
        branch = cfg["branch"]
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, params={"ref": branch})
        sha = res.json().get("sha") if res.status_code == 200 else None
        with open(filename, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode("utf-8")
        payload = {"message": f"🤖 Automated Dashboard Sync: Update {filename}", "content": encoded_content, "branch": branch}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception: pass

def get_starter_tasks():
    return {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup Check", "Weekly App Sync", "Monthly Budget Check"],
        "task_description": ["Review code checklist.", "Verify remote logs.", "Export statements."],
        "task_url": ["", "", ""],
        "frequency": ["Daily", "Weekly", "Monthly"],
        "is_recurring": ["Yes", "Yes", "Yes"],
        "last_completed": [(datetime.now() - timedelta(days=2)).strftime(STORAGE_DATE_FORMAT), (datetime.now() - timedelta(days=8)).strftime(STORAGE_DATE_FORMAT), (datetime.now() - timedelta(days=32)).strftime(STORAGE_DATE_FORMAT)],
        "task_screenshot_b64": ["", "", ""],
        "task_priority": [3, 2, 1]
    }

def verify_and_align_columns(df_obj, filename, fallback_cols):
    updated = False
    for col in fallback_cols:
        if col not in df_obj.columns:
            df_obj[col] = 3 if col == "task_priority" else ""
            updated = True
    if updated:
        df_obj.to_csv(filename, index=False)
        push_to_github(filename)
    return df_obj

# Load/Initialize Databases
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(get_starter_tasks())
    df.to_csv(DB_FILE, index=False)
    push_to_github(DB_FILE)
else:
    df = pd.read_csv(DB_FILE)
    df = verify_and_align_columns(df, DB_FILE, ["task_url", "is_recurring", "task_screenshot_b64", "task_priority"])
    df["task_url"] = df["task_url"].fillna("").astype(str)
    df["is_recurring"] = df["is_recurring"].fillna("Yes").astype(str)
    df["task_screenshot_b64"] = df["task_screenshot_b64"].fillna("").astype(str)
    try:
        df["task_priority"] = pd.to_numeric(df["task_priority"].fillna(3)).astype(int)
    except Exception:
        df["task_priority"] = 3

REQUIRED_LOG_COLUMNS = ["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"]

if not os.path.exists(EOD_FILE) or os.path.getsize(EOD_FILE) == 0:
    eod_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS)
    eod_df.to_csv(EOD_FILE, index=False)
    push_to_github(EOD_FILE)
else:
    eod_df = pd.read_csv(EOD_FILE)
    eod_df = verify_and_align_columns(eod_df, EOD_FILE, REQUIRED_LOG_COLUMNS)

if not os.path.exists(ARCHIVE_FILE) or os.path.getsize(ARCHIVE_FILE) == 0:
    archive_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS)
    archive_df.to_csv(ARCHIVE_FILE, index=False)
    push_to_github(ARCHIVE_FILE)
else:
    archive_df = pd.read_csv(ARCHIVE_FILE)
    archive_df = verify_and_align_columns(archive_df, ARCHIVE_FILE, REQUIRED_LOG_COLUMNS)

if not os.path.exists(NOTES_FILE) or os.path.getsize(NOTES_FILE) == 0:
    notes_df = pd.DataFrame(columns=["note_id", "title", "details", "event_date"])
    notes_df.to_csv(NOTES_FILE, index=False)
    push_to_github(NOTES_FILE)
else:
    notes_df = pd.read_csv(NOTES_FILE)

if not os.path.exists(PRIORITIES_FILE) or os.path.getsize(PRIORITIES_FILE) == 0:
    prio_df = pd.DataFrame(columns=["prio_id", "item_text"])
    prio_df.to_csv(PRIORITIES_FILE, index=False)
    push_to_github(PRIORITIES_FILE)
else:
    prio_df = pd.read_csv(PRIORITIES_FILE)

def save_and_push(dataframe, filename):
    dataframe.to_csv(filename, index=False)
    push_to_github(filename)

def get_days_interval(freq_string):
    if freq_string == "Daily": return 1
    elif freq_string == "Weekly": return 7
    else: return 30

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except ValueError:
        try: return datetime.strptime(str(date_str), DATE_FORMAT).date()
        except ValueError: return datetime.now().date()

# NEW ROLLOVER LOGIC: Calculates effective date for display
def get_effective_due_date(last_completed_str, frequency):
    last_comp_date = parse_date_safely(last_completed_str)
    interval = get_days_interval(frequency)
    next_due_date = last_comp_date + timedelta(days=interval)
    # If it is past due, return today, otherwise return the actual due date
    return today if next_due_date < today else next_due_date

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

main_layout_frame, right_buffer_column = st.columns([12, 1])

with main_layout_frame:
    st.header("📅 Monthly Overview")
    calendar_events = []
    
    for index, row in df.iterrows():
        # Using the rollover-aware logic for calendar display
        effective_due = get_effective_due_date(row.get('last_completed'), row.get('frequency'))
        is_overdue = today > effective_due
        
        calendar_events.append({
            "title": f"⚠️ Due: {row.get('task_name', 'Task')}" if is_overdue else f"{'📌' if str(row.get('is_recurring', 'Yes')) == 'No' else '🔄'} {row.get('task_name', 'Task')}", 
            "start": effective_due.strftime(STORAGE_DATE_FORMAT), 
            "end": effective_due.strftime(STORAGE_DATE_FORMAT), 
            "backgroundColor": "#EF4444" if is_overdue else "#1E3A8A",
            "borderColor": "#EF4444" if is_overdue else "#1E3A8A",
            "allDay": True
        })
    
    for index, row in notes_df.iterrows():
        n_date = parse_date_safely(row['event_date']).strftime(STORAGE_DATE_FORMAT)
        calendar_events.append({"title": f"📌 {row['title']}", "start": n_date, "end": n_date, "backgroundColor": "#334155", "borderColor": "#334155", "allDay": True})
    
    calendar(events=calendar_events, options={"initialView": "dayGridMonth", "headerToolbar": { "left": "prev,next today", "center": "title", "right": "" }, "editable": False, "selectable": True, "height": "auto", "dayMaxEvents": True, "moreLinkClick": "popover"}, key="monthly_grid_view")

    # --- TABBED CONTENT ---
    # (The rest of your existing logic remains perfectly compatible below this point)
    st.subheader("🖥️ Command Center 🖥️")
    # ... your existing logic continues from here ...
    st.info("System Ready. Unfinished tasks automatically roll over in the calendar view.")
