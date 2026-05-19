import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar  # Imports the visual calendar component

# 1. Page Configuration
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database File Setup
DB_FILE = "tasks_db.csv"
DATE_FORMAT = "%d/%m/%Y"

if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

# Load existing tasks or initialize defaults
if not os.path.exists(DB_FILE):
    starter_data = {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup Check", "Weekly App Sync", "Monthly Budget Check"],
        "task_description": [
            "Review code checklist.",
            "Verify remote logs and verify files.",
            "Export statement values to master table."
        ],
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

def save_db(dataframe):
    dataframe.to_csv(DB_FILE, index=False)

def get_days_interval(freq_string):
    if freq_string == "Daily": return 1
    elif freq_string == "Weekly": return 7
    else: return 30

st.title("🗓️ Personal Tracker & Interactive Calendar")
st.markdown("---")

today = datetime.now().date()

# Create side-by-side split screen panels
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: ACTIONABLE TRACKER INTERFACE
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
                with st.expander("📄 Instructions"):
                    st.write(row['task_description'])
            with col_btn:
                if st.button("Complete", key=f"remind_btn_{row['task_id']}"):
                    df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                    save_db(df)
                    st.rerun()
                    
    if not reminders_found:
        st.success("🎉 All routines are current and up to date!")
        
    st.markdown("---")
    
    # --- Quick Edit Layout ---
    st.subheader("⚙️ Edit Schedule Items")
    for index, row in df.iterrows():
        ec1, ec2, ec3 = st.columns([3, 1, 1])
        if st.session_state.editing_task_id == row['task_id']:
            with ec1:
                edit_name = st.text_input("Name", value=row['task_name'], key=f"en_{row['task_id']}")
                edit_desc = st.text_area("Instructions", value=row['task_description'], key=f"ed_{row['task_id']}")
            with ec2:
                edit_freq = st.selectbox("Cycle", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row['frequency']), key=f"ef_{row['task_id']}")
            with ec3:
                if st.button("💾", key=f"s_{row['task_id']}"):
                    df.at[index, 'task_name'] = edit_name
                    df.at[index, 'task_description'] = edit_desc
                    df.at[index, 'frequency'] = edit_freq
                    save_db(df)
                    st.session_state.editing_task_id = None
                    st.rerun()
        else:
            with ec1:
                st.write(f"**{row['task_name']}** ({row['frequency']})")
            with ec2:
                if st.button("✏️", key=f"em_{row['task_id']}"):
                    st.session_state.editing_task_id = row['task_id']
                    st.rerun()
            with ec3:
                if st.button("🗑️", key=f"d_{row['task_id']}"):
                    df = df[df['task_id'] != row['task_id']]
                    save_db(df)
                    st.rerun()
        st.markdown("<hr style='margin:0.1em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Task Creation Engine ---
    st.subheader("➕ Create Custom Item")
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
            save_db(df)
            st.rerun()

# ------------------------------------------
# RIGHT PANEL: FULL MONTH INTERACTIVE CALENDAR GRID
# ------------------------------------------
with right_panel:
    st.header("📅 Visual Monthly Calendar")
    
    calendar_events = []
    
    for index, row in df.iterrows():
        base_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
        target_span = get_days_interval(row['frequency'])
        next_due = base_date + timedelta(days=target_span)
        
        # Color code events: Red if overdue, Blue if safe
        is_overdue = today >= next_due
        event_color = "#FF4B4B" if is_overdue else "#1C83E1"
        
        # Format events into the exact calendar schema template
        calendar_events.append({
            "title": f"⚠️ {row['task_name']}" if is_overdue else row['task_name'],
            "start": next_due.strftime("%Y-%m-%d"),
            "end": next_due.strftime("%Y-%m-%d"),
            "backgroundColor": event_color,
            "borderColor": event_color,
            "allDay": True
        })
        
    # Calendar UI Configurations Options
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
    
    # Render the physical monthly calendar widget
    calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
