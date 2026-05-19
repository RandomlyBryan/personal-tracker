import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar

# 1. Page Configuration
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database Files Setup
DB_FILE = "tasks_db.csv"
NOTES_FILE = "calendar_notes.csv"  # New database file for one-time notes/meetings
DATE_FORMAT = "%d/%m/%Y"

if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

# Load/Initialize Recurring Tasks Database
if not os.path.exists(DB_FILE):
    starter_data = {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup Check", "Weekly App Sync", "Monthly Budget Check"],
        "task_description": ["Review code checklist.", "Verify remote logs.", "Export statements."],
        "frequency": ["Daily", "Weekly", "Monthly"],
        "last_completed": [
            (datetime.now() - timedelta(days=2)).strftime(DATE_FORMAT), 
            (datetime.now() - timedelta(days=8)).strftime(DATE_FORMAT), 
            (datetime.now() - timedelta(days=32)).strftime(DATE_FORMAT)
        ]
    }
    df = pd.DataFrame(starter_data)
    df.to_csv(DB_FILE, index=False)
else:
    df = pd.read_csv(DB_FILE)

# Load/Initialize One-Time Calendar Notes Database
if not os.path.exists(NOTES_FILE):
    notes_df = pd.DataFrame(columns=["note_id", "title", "details", "event_date"])
    notes_df.to_csv(NOTES_FILE, index=False)
else:
    notes_df = pd.read_csv(NOTES_FILE)

def save_db(dataframe, filename):
    dataframe.to_csv(filename, index=False)

def get_days_interval(freq_string):
    if freq_string == "Daily": return 1
    elif freq_string == "Weekly": return 7
    else: return 30

st.title("🗓️ Personal Tracker & Interactive Calendar")
st.markdown("---")

today = datetime.now().date()

# Side-by-side split layout
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: MANAGER & FORMS
# ------------------------------------------
with left_panel:
    st.header("📋 Task & Routine Manager")
    
    # --- Urgent Alerts ---
    st.subheader("🔔 Urgent Updates")
    reminders_found = False
    
    for index, row in df.iterrows():
        last_comp_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
        days_since = (today - last_comp_date).days
        needed_days = get_days_interval(row['frequency'])
        
        if days_since >= needed_days:
            reminders_found = True
            col_text, col_btn = st.columns([3, 1])
            with col_text:
                st.warning(f"**{row['task_name']}** due! ({days_since} days since update)")
            with col_btn:
                if st.button("Complete", key=f"remind_btn_{row['task_id']}"):
                    df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                    save_db(df, DB_FILE)
                    st.rerun()
                    
    if not reminders_found:
        st.success("🎉 All routines are current and up to date!")
        
    st.markdown("---")
    
    # --- Form 1: Add Recurring Task ---
    st.subheader("➕ Add Custom Recurring Task")
    with st.form("new_task_form", clear_on_submit=True):
        new_name = st.text_input("Task Name / Title")
        new_desc = st.text_area("Task Instructions")
        new_freq = st.selectbox("Interval Cycle", ["Daily", "Weekly", "Monthly"])
        submitted = st.form_submit_button("Add to Rotation")
        
        if submitted and new_name:
            new_id = int(df['task_id'].max() + 1) if not df.empty else 1
            days_back = get_days_interval(new_freq) + 1
            default_past = today - timedelta(days=days_back)
            
            new_row = {
                "task_id": new_id,
                "task_name": new_name,
                "task_description": new_desc if new_desc else "No instructions provided.",
                "frequency": new_freq,
                "last_completed": default_past.strftime(DATE_FORMAT)
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_db(df, DB_FILE)
            st.rerun()

    st.markdown("---")

    # --- Form 2: Add One-Time Calendar Note / Meeting ---
    st.subheader("📌 Add Calendar Note / Meeting Schedule")
    with st.form("new_note_form", clear_on_submit=True):
        note_title = st.text_input("Event / Meeting Title (e.g., Sync with Team)")
        note_details = st.text_area("Notes / Agenda Details")
        note_date = st.date_input("Event Date", value=today)
        submitted_note = st.form_submit_button("Pin to Calendar")
        
        if submitted_note and note_title:
            new_note_id = int(notes_df['note_id'].max() + 1) if not notes_df.empty else 1
            new_note_row = {
                "note_id": new_note_id,
                "title": note_title,
                "details": note_details if note_details else "",
                "event_date": note_date.strftime("%Y-%m-%d") # Store as ISO string for calendar matching
            }
            notes_df = pd.concat([notes_df, pd.DataFrame([new_note_row])], ignore_index=True)
            save_db(notes_df, NOTES_FILE)
            st.success(f"Pinned event: {note_title}")
            st.rerun()

# ------------------------------------------
# RIGHT PANEL: VISUAL MONTHLY CALENDAR GRID
# ------------------------------------------
with right_panel:
    st.header("📅 Visual Monthly Calendar")
    
    calendar_events = []
    
    # 1. Process and load the Recurring Tasks
    for index, row in df.iterrows():
        base_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
        target_span = get_days_interval(row['frequency'])
        next_due = base_date + timedelta(days=target_span)
        
        is_overdue = today >= next_due
        event_color = "#FF4B4B" if is_overdue else "#1C83E1"
        
        calendar_events.append({
            "title": f"⚠️ Due: {row['task_name']}" if is_overdue else f"🔄 {row['task_name']}",
            "start": next_due.strftime("%Y-%m-%d"),
            "end": next_due.strftime("%Y-%m-%d"),
            "backgroundColor": event_color,
            "borderColor": event_color,
            "allDay": True
        })
        
    # 2. Process and load the One-Time Notes / Meetings
    for index, row in notes_df.iterrows():
        # Purple color theme to visually distinguish meetings/notes from tasks
        note_color = "#7A41F3" 
        
        calendar_events.append({
            "title": f"📌 {row['title']}",
            "start": str(row['event_date']),
            "end": str(row['event_date']),
            "backgroundColor": note_color,
            "borderColor": note_color,
            "allDay": True
        })
        
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": ""
        },
        "editable": False,
        "selectable": True
    }
    
    # Display the calendar with both datasets merged
    calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
    
    # --- Quick list layout to see text details of pinned notes below calendar ---
    if not notes_df.empty:
        st.subheader("📝 Quick Look: Upcoming Pinned Notes")
        for index, row in notes_df.iterrows():
            formatted_note_date = datetime.strptime(row['event_date'], "%Y-%m-%d").strftime(DATE_FORMAT)
            with st.expander(f"📌 {formatted_note_date} — {row['title'] Bill}"):
                st.write(row['details'])
                if st.button("Delete Note", key=f"del_note_{row['note_id']}"):
                    notes_df = notes_df[notes_df['note_id'] != row['note_id']]
                    save_db(notes_df, NOTES_FILE)
                    st.rerun()
