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

st.set_page_config(page_title="Personal Task Tracker", layout="wide")

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
        payload = {"message": f"🤖 Automated Dashboard Sync: {filename}", "content": encoded_content, "branch": branch}
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

def load_data(filename, default_df, cols):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        default_df.to_csv(filename, index=False)
        return default_df
    df = pd.read_csv(filename)
    return verify_and_align_columns(df, filename, cols)

df = load_data(DB_FILE, pd.DataFrame(get_starter_tasks()), ["task_url", "is_recurring", "task_screenshot_b64", "task_priority"])
eod_df = load_data(EOD_FILE, pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"]), ["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"])
archive_df = load_data(ARCHIVE_FILE, pd.DataFrame(columns=eod_df.columns), eod_df.columns)
notes_df = load_data(NOTES_FILE, pd.DataFrame(columns=["note_id", "title", "details", "event_date"]), ["note_id", "title", "details", "event_date"])
prio_df = load_data(PRIORITIES_FILE, pd.DataFrame(columns=["prio_id", "item_text"]), ["prio_id", "item_text"])

def save_and_push(dataframe, filename):
    dataframe.to_csv(filename, index=False)
    push_to_github(filename)

def get_days_interval(freq):
    return {"Daily": 1, "Weekly": 7, "Monthly": 30}.get(freq, 1)

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except ValueError:
        try: return datetime.strptime(str(date_str), DATE_FORMAT).date()
        except ValueError: return datetime.now().date()

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

main_layout_frame, _ = st.columns([12, 1])
with main_layout_frame:
    st.header("📋 Command Center")
    tab_alerts, tab_add, tab_manage, tab_eod, tab_archive = st.tabs(["🚨 Pending", "➕ New", "⚙️ Manage", "📝 EOD", "📊 History"])
    
    with tab_alerts:
        for index, row in df.sort_values(by="task_priority", ascending=False).iterrows():
            last_comp_date = parse_date_safely(row['last_completed'])
            if (today - last_comp_date).days >= get_days_interval(row['frequency']):
                st.markdown(f"### **{row['task_name']}** <span class='stars-container'>{'⭐' * int(row['task_priority'])}</span>", unsafe_allow_html=True)
                with st.form(key=f"form_{row['task_id']}"):
                    result_notes = st.text_area("Action Notes:", key=f"res_{row['task_id']}")
                    if st.form_submit_button("Done"):
                        new_log_row = {"log_id": eod_df['log_id'].max() + 1 if not eod_df.empty else 1, "task_title": row['task_name'], "bullet_text": result_notes or "Completed.", "log_date": today.strftime(STORAGE_DATE_FORMAT), "task_links": row['task_url'], "screenshot_b64": row['task_screenshot_b64'], "doc_attachment_b64": "", "doc_attachment_name": ""}
                        eod_df = pd.concat([eod_df, pd.DataFrame([new_log_row])], ignore_index=True)
                        save_and_push(eod_df, EOD_FILE)
                        if row['is_recurring'] == "No": df = df.drop(index)
                        else: df.at[index, 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                        save_and_push(df, DB_FILE)
                        st.rerun()

    with tab_add:
        with st.form("new_note_form", clear_on_submit=True):
            note_title = st.text_input("Title")
            note_date = st.date_input("Date")
            if st.form_submit_button("Pin"):
                new_note_id = int(notes_df['note_id'].max() + 1) if not notes_df.empty else 1
                notes_df = pd.concat([notes_df, pd.DataFrame([{"note_id": new_note_id, "title": note_title, "details": "", "event_date": note_date.strftime(STORAGE_DATE_FORMAT)}])], ignore_index=True)
                save_and_push(notes_df, NOTES_FILE)
                st.rerun()

    with tab_eod:
        if st.button("Clear Logged Work"):
            archive_df = pd.concat([archive_df, eod_df], ignore_index=True)
            save_and_push(archive_df, ARCHIVE_FILE)
            eod_df = pd.DataFrame(columns=eod_df.columns)
            save_and_push(eod_df, EOD_FILE)
            st.rerun()
        st.code(eod_df.to_string())
