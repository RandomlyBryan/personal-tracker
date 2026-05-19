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

# ==========================================
# CUSTOM CSS: OVERRIDE ALL FONTS TO GEORGIA
# ==========================================
st.markdown(
    """
    <style>
        /* This applies Georgia font to the main text, markdown, headers, and tabs */
        html, body, [data-testid="stAppViewContainer"], .main, h1, h2, h3, h4, h5, h6, p, label, .stTabs button {
            font-family: 'Georgia', serif !important;
        }
        /* This applies it specifically inside interactive input text fields */
        input, textarea, select {
            font-family: 'Georgia', serif !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. Database Files Setup
DB_FILE = "tasks_db.csv"
NOTES_FILE = "calendar_notes.csv"
DATE_FORMAT = "%d/%m/%Y"

if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

# Load/Initialize Databases
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

st.title("🗓️ Personal Tracker Dashboard")
st.markdown("---")

today = datetime.now().date()

# Side-by-side split layout
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: COMPACT TABBED WORKSPACE
# ------------------------------------------
with left_panel:
    st.header("📋 Workspace Control")
    
    tab_alerts, tab_add, tab_manage = st.tabs(["🚨 Pending Actions", "➕ Add New", "⚙️ Manage Existing"])
    
    # --- TAB 1: URGENT ALERTS ---
    with tab_alerts:
        st.subheader("Items Due For Update")
        reminders_found = False
        
        for index, row in df.iterrows():
            last_comp_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
            days_since = (today - last_comp_date).days
            needed_days = get_days_interval(row['frequency'])
            
            if days_since >= needed_days:
                reminders_found = True
                col_text, col_btn = st.columns([3, 1])
                with col_text:
                    st.warning(f"**{row['task_name']}** ({row['frequency']})")
                    with st.expander("📄 View Details"):
                        st.write(row['task_description'])
                with col_btn:
                    if st.button("Done", key=f"remind_btn_{row['task_id']}"):
                        df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                        save_db(df, DB_FILE)
                        st.rerun()
                        
        if not reminders_found:
            st.success("🎉 Everything is running on schedule!")
            
    # --- TAB 2: DATA CREATION FORMS ---
    with tab_add:
        sub_tab_task, sub_tab_note = st.tabs(["🔄 Recurring Routine", "📌 One-Time Note"])
        
        with sub_tab_task:
            with st.form("new_task_form", clear_on_submit=True):
                new_name = st.text_input("Task Title")
                new_desc = st.text_area("Instructions")
                new_freq = st.selectbox("Interval", ["Daily", "Weekly", "Monthly"])
                submitted = st.form_submit_button("Save Routine")
                
                if submitted and new_name:
                    new_id = int(df['task_id'].max() + 1) if not df.empty else 1
                    days_back = get_days_interval(new_freq) + 1
                    default_past = today - timedelta(days=days_back)
                    
                    new_row = {
                        "task_id": new_id,
                        "task_name": new_name,
                        "task_description": new_desc if new_desc else "No instructions.",
                        "frequency": new_freq,
                        "last_completed": default_past.strftime(DATE_FORMAT)
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_db(df, DB_FILE)
                    st.rerun()

        with sub_tab_note:
            with st.form("new_note_form", clear_on_submit=True):
                note_title = st.text_input("Meeting / Event Title")
                note_details = st.text_area("Agenda Notes")
                note_date = st.date_input("Event Date", value=today)
                submitted_note = st.form_submit_button("Pin to Calendar")
                
                if submitted_note and note_title:
                    new_note_id = int(notes_df['note_id'].max() + 1) if not notes_df.empty else 1
                    new_note_row = {
                        "note_id": new_note_id,
                        "title": note_title,
                        "details": note_details if note_details else "",
                        "event_date": note_date.strftime("%Y-%m-%d")
                    }
                    notes_df = pd.concat([notes_df, pd.DataFrame([new_note_row])], ignore_index=True)
                    save_db(notes_df, NOTES_FILE)
                    st.rerun()

    # --- TAB 3: MAINTENANCE LISTS (EDIT & DELETE) ---
    with tab_manage:
        st.subheader("Edit & Delete Settings")
        m_task, m_note = st.tabs(["Rotations", "Pinned Notes"])
        
        with m_task:
            for index, row in df.iterrows():
                ec1, ec2, ec3 = st.columns([3, 1, 1])
                if st.session_state.editing_task_id == row['task_id']:
                    with ec1:
                        edit_name = st.text_input("Name", value=row['task_name'], key=f"en_{row['task_id']}", label_visibility="collapsed")
                        edit_desc = st.text_area("Desc", value=row['task_description'], key=f"ed_{row['task_id']}", label_visibility="collapsed")
                    with ec2:
                        edit_freq = st.selectbox("Freq", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row['frequency']), key=f"ef_{row['task_id']}", label_visibility="collapsed")
                    with ec3:
                        if st.button("💾", key=f"s_{row['task_id']}"):
                            df.at[index, 'task_name'] = edit_name
                            df.at[index, 'task_description'] = edit_desc
                            df.at[index, 'frequency'] = edit_freq
                            save_db(df, DB_FILE)
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
                            save_db(df, DB_FILE)
                            st.rerun()
                st.markdown("<hr style='margin:0.05em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

        with m_note:
            if notes_df.empty:
                st.info("No temporary calendar notes pinned.")
            else:
                for index, row in notes_df.iterrows():
                    nc1, nc2 = st.columns([4, 1])
                    with nc1:
                        f_date = datetime.strptime(row['event_date'], "%Y-%m-%d").strftime(DATE_FORMAT)
                        st.write(f"📌 **{f_date}** — {row['title']}")
                    with nc2:
                        if st.button("🗑️", key=f"del_note_{row['note_id']}"):
                            notes_df = notes_df[notes_df['note_id'] != row['note_id']]
                            save_db(notes_df, NOTES_FILE)
                            st.rerun()

# ------------------------------------------
# RIGHT PANEL: FLUID VISUAL CALENDAR
# ------------------------------------------
with right_panel:
    st.header("📅 Monthly Overview")
    
    calendar_events = []
    
    # 1. Plot Tasks
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
        
    # 2. Plot Notes
    for index, row in notes_df.iterrows():
        calendar_events.append({
            "title": f"📌 {row['title']}",
            "start": str(row['event_date']),
            "end": str(row['event_date']),
            "backgroundColor": "#7A41F3",
            "borderColor": "#7A41F3",
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
        "selectable": True,
        "height": "auto"
    }
    
    calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
