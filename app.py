import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar

# 1. Page Configuration
st.set_page_config(page_title="Personal Task Tracker", layout="wide")

# CUSTOM CSS: OVERRIDE ALL FONTS TO GEORGIA
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .main, h1, h2, h3, h4, h5, h6, p, label, .stTabs button {
            font-family: 'Georgia', serif !important;
        }
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
EOD_FILE = "eod_temp_logs.csv"
DATE_FORMAT = "%d/%m/%Y"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

# Initialize temporary memory states
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "editing_note_id" not in st.session_state:
    st.session_state.editing_note_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

# Load/Initialize Databases
if not os.path.exists(DB_FILE):
    starter_data = {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup Check", "Weekly App Sync", "Monthly Budget Check"],
        "task_description": ["Review code checklist.", "Verify remote logs.", "Export statements."],
        "task_url": ["", "", ""],
        "frequency": ["Daily", "Weekly", "Monthly"],
        "last_completed": [
            (datetime.now() - timedelta(days=2)).strftime(STORAGE_DATE_FORMAT), 
            (datetime.now() - timedelta(days=8)).strftime(STORAGE_DATE_FORMAT), 
            (datetime.now() - timedelta(days=32)).strftime(STORAGE_DATE_FORMAT)
        ]
    }
    df = pd.DataFrame(starter_data)
    df.to_csv(DB_FILE, index=False)
else:
    df = pd.read_csv(DB_FILE)
    if "task_url" not in df.columns:
        df["task_url"] = ""

if not os.path.exists(NOTES_FILE):
    notes_df = pd.DataFrame(columns=["note_id", "title", "details", "event_date"])
    notes_df.to_csv(NOTES_FILE, index=False)
else:
    notes_df = pd.read_csv(NOTES_FILE)

if not os.path.exists(EOD_FILE):
    eod_df = pd.DataFrame(columns=["log_id", "bullet_text"])
    eod_df.to_csv(EOD_FILE, index=False)
else:
    eod_df = pd.read_csv(EOD_FILE)

def save_db(dataframe, filename):
    dataframe.to_csv(filename, index=False)

def get_days_interval(freq_string):
    if freq_string == "Daily": return 1
    elif freq_string == "Weekly": return 7
    else: return 30

def parse_date_safely(date_str):
    try:
        return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except ValueError:
        try:
            return datetime.strptime(str(date_str), DATE_FORMAT).date()
        except ValueError:
            return datetime.now().date()

# Centered main screen title
st.markdown(
    "<h1 style='text-align: center; font-family: Georgia, serif;'>🗓️ Personal Tracker Dashboard</h1>", 
    unsafe_allow_html=True
)
st.markdown("---")

today = datetime.now().date()

# Side-by-side split layout
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: COMPACT TABBED WORKSPACE WITH EOD ENGINE
# ------------------------------------------
with left_panel:
    st.header("📋 Command Center")
    
    tab_alerts, tab_eod, tab_add, tab_manage = st.tabs(["🚨 Pending Tasks", "📝 EOD Report", "➕ New Task", "⚙️ Existing Task"])
    
    # --- TAB 1: URGENT ALERTS ---
    with tab_alerts:
        st.subheader("Items Due For Update")
        reminders_found = False
        
        for index, row in df.iterrows():
            last_comp_date = parse_date_safely(row['last_completed'])
            days_since = (today - last_comp_date).days
            needed_days = get_days_interval(row['frequency'])
            
            if days_since >= needed_days:
                reminders_found = True
                col_text, col_btn = st.columns([3, 1])
                with col_text:
                    st.warning(f"**{row['task_name']}** ({row['frequency']})")
                    with st.expander("📄 View Details & Resources"):
                        st.write(row['task_description'])
                        task_link = str(row.get('task_url', '')).strip()
                        if task_link and task_link != "nan" and task_link != "":
                            st.link_button("🔗 Open Direct Link", url=task_link, use_container_width=True)
                with col_btn:
                    if st.button("Done", key=f"remind_btn_{row['task_id']}"):
                        df.at[index, 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                        save_db(df, DB_FILE)
                        st.rerun()
                        
        if not reminders_found:
            st.success("🎉 Everything is running on schedule!")
            
    # --- TAB 2: EOD REPORT LOG BUILDER ---
    with tab_eod:
        st.subheader("Daily Completed Task Tracker")
        
        st.markdown("**📋 Quick Copy**")
        st.code("Bryan Reyes", language=None)
        st.code("work.bryanc@gmail.com", language=None)
        st.code("Marketing & Reporting VA", language=None)
        
        st.markdown("---")
        st.write("Type out your tasks below as you finish them. They will accumulate into a ready-to-copy report block.")

        with st.form("eod_add_form", clear_on_submit=True):
            log_input = st.text_input("Enter completed action item / accomplishment:")
            add_bullet = st.form_submit_button("Stage Accomplishment")
            
            if add_bullet and log_input:
                new_log_id = int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1
                new_log_row = {"log_id": new_log_id, "bullet_text": log_input.strip()}
                eod_df = pd.concat([eod_df, pd.DataFrame([new_log_row])], ignore_index=True)
                save_db(eod_df, EOD_FILE)
                st.rerun()

        st.markdown("---")

        emp_header = (
            f"Date: {today.strftime(DATE_FORMAT)}\n"
            f"----------------------------------------\n"
            f"Completed Tasks & Actions Log:\n"
        )

        if not eod_df.empty:
            bullet_lines = "\n".join([f"• {row['bullet_text']}" for _, row in eod_df.iterrows()])
            compiled_report = f"{emp_header}{bullet_lines}"
        else:
            compiled_report = f"{emp_header}• (No work logged yet today. Use the form above to add lines.)"
            
        st.markdown("**Your Compiled EOD Summary Output:**")
        st.code(compiled_report, language=None)
        
        if not eod_df.empty:
            st.markdown(" ")
            col_space, col_clear = st.columns([3, 1])
            with col_clear:
                if st.button("🗑️ Clear Staged Data", help="Wipe out current logs to reset for a new work day"):
                    eod_df = pd.DataFrame(columns=["log_id", "bullet_text"])
                    save_db(eod_df, EOD_FILE)
                    st.rerun()
                    
            with st.expander("✏️ Modify Individual Staged Bullets"):
                for idx, r in eod_df.iterrows():
                    b_col1, b_col2 = st.columns([5, 1])
                    with b_col1:
                        st.write(f"- {r['bullet_text']}")
                    with b_col2:
                        if st.button("❌", key=f"del_b_{r['log_id']}", help="Remove this single bullet"):
                            eod_df = eod_df[eod_df['log_id'] != r['log_id']]
                            save_db(eod_df, EOD_FILE)
                            st.rerun()

    # --- TAB 3: DATA CREATION FORMS ---
    with tab_add:
        sub_tab_task, sub_tab_note = st.tabs(["🔄 Recurring Routine", "📌 One-Time Note"])
        
        with sub_tab_task:
            with st.form("new_task_form", clear_on_submit=True):
                new_name = st.text_input("Task Title")
                new_desc = st.text_area("Instructions")
                new_url = st.text_input("Task URL Link (Optional - e.g. Google Sheet Link)")
                new_freq = st.selectbox("Interval", ["Daily", "Weekly", "Monthly"])
                start_date = st.date_input("Routine Start Date", value=today)
                submitted = st.form_submit_button("Save Routine")
                
                if submitted and new_name:
                    new_id = int(df['task_id'].max() + 1) if not df.empty else 1
                    
                    new_row = {
                        "task_id": new_id,
                        "task_name": new_name,
                        "task_description": new_desc if new_desc else "No instructions.",
                        "task_url": new_url.strip(),
                        "frequency": new_freq,
                        "last_completed": start_date.strftime(STORAGE_DATE_FORMAT)
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
                        "event_date": note_date.strftime(STORAGE_DATE_FORMAT)
                    }
                    notes_df = pd.concat([notes_df, pd.DataFrame([new_note_row])], ignore_index=True)
                    save_db(notes_df, NOTES_FILE)
                    st.rerun()

    # --- TAB 4: MAINTENANCE LISTS (EDIT & DELETE) ---
    with tab_manage:
        st.subheader("Edit & Delete Settings")
        m_task, m_note = st.tabs(["Rotations", "Calendar Notes"])
        
        with m_task:
            for index, row in df.iterrows():
                ec1, ec2, ec3 = st.columns([3, 1, 1])
                current_task_date = parse_date_safely(row['last_completed'])
                
                if st.session_state.editing_task_id == row['task_id']:
                    with ec1:
                        edit_name = st.text_input("Name", value=row['task_name'], key=f"en_{row['task_id']}", label_visibility="collapsed")
                        edit_desc = st.text_area("Desc", value=row['task_description'], key=f"ed_{row['task_id']}", label_visibility="collapsed")
                        edit_url = st.text_input("URL Link", value=str(row.get('task_url', '') if pd.notna(row.get('task_url', '')) else ''), key=f"eurl_{row['task_id']}")
                    with ec2:
                        edit_freq = st.selectbox("Freq", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row['frequency']), key=f"ef_{row['task_id']}", label_visibility="collapsed")
                        edit_t_date = st.date_input("Edit Start Date", value=current_task_date, key=f"etd_{row['task_id']}", label_visibility="collapsed")
                    with ec3:
                        if st.button("💾", key=f"s_{row['task_id']}"):
                            df.at[index, 'task_name'] = edit_name
                            df.at[index, 'task_description'] = edit_desc
                            df.at[index, 'task_url'] = edit_url.strip()
                            df.at[index, 'frequency'] = edit_freq
                            df.at[index, 'last_completed'] = edit_t_date.strftime(STORAGE_DATE_FORMAT)
                            save_db(df, DB_FILE)
                            st.session_state.editing_task_id = None
                            st.rerun()
                else:
                    with ec1:
                        st.write(f"**{row['task_name']}** ({row['frequency']})")
                        st.caption(f"Baseline Date: {current_task_date.strftime(DATE_FORMAT)}")
                        current_url_val = str(row.get('task_url', '')).strip()
                        if current_url_val and current_url_val != "nan" and current_url_val != "":
                            st.caption(f"🔗 Link: {current_url_val}")
                    with ec2:
                        if st.button("✏️", key=f"em_{row['task_id']}"):
                            st.session_state.editing_task_id = row['task_id']
                            st.rerun()
                    with ec3:
                        if st.button("🗑️", key=f"d_{row['task_id']}"):
                            df = df[df['task_id'] != row['task_id']]
                            save_db(df, DB_FILE)
                            st.rerun()
                # FIXED: Changed 'unsafe_allowed_html' to 'unsafe_allow_html' to stop the crash
                st.markdown("<hr style='margin:0.05em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

        with m_note:
            if notes_df.empty:
                st.info("No temporary calendar notes pinned.")
            else:
                for index, row in notes_df.iterrows():
                    nc1, nc2, nc3 = st.columns([3, 1, 1])
                    
                    if st.session_state.editing_note_id == row['note_id']:
                        current_note_date = parse_date_safely(row['event_date'])
                        with nc1:
                            edit_note_title = st.text_input("Edit Note Title", value=row['title'], key=f"ent_{row['note_id']}", label_visibility="collapsed")
                            edit_note_details = st.text_area("Edit Note Details", value=row['details'], key=f"end_{row['note_id']}", label_visibility="collapsed")
                        with nc2:
                            edit_note_date = st.date_input("Edit Note Date", value=current_note_date, key=f"endate_{row['note_id']}", label_visibility="collapsed")
                        with nc3:
                            if st.button("💾", key=f"s_note_{row['note_id']}"):
                                notes_df.at[index, 'title'] = edit_note_title
                                notes_df.at[index, 'details'] = edit_note_details
                                notes_df.at[index, 'event_date'] = edit_note_date.strftime(STORAGE_DATE_FORMAT)
                                save_db(notes_df, NOTES_FILE)
                                st.session_state.editing_note_id = None
                                st.rerun()
                            if st.button("❌", key=f"c_note_{row['note_id']}"):
                                st.session_state.editing_note_id = None
                                st.rerun()
                    else:
                        with nc1:
                            f_date = parse_date_safely(row['event_date']).strftime(DATE_FORMAT)
                            st.write(f"📌 **{f_date}** — {row['title']}")
                            if row['details']:
                                with st.expander("📄 View Agenda Notes"):
                                    st.write(row['details'])
                        with nc2:
                            if st.button("✏️", key=f"em_note_{row['note_id']}"):
                                st.session_state.editing_note_id = row['note_id']
                                st.rerun()
                        with nc3:
                            if st.button("🗑️", key=f"del_note_{row['note_id']}"):
                                notes_df = notes_df[notes_df['note_id'] != row['note_id']]
                                save_db(notes_df, NOTES_FILE)
                                st.rerun()
                    # FIXED: Changed 'unsafe_allowed_html' to 'unsafe_allow_html' to stop the crash
                    st.markdown("<hr style='margin:0.05em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

# ------------------------------------------
# RIGHT PANEL: FLUID VISUAL CALENDAR
# ------------------------------------------
with right_panel:
    st.header("📅 Monthly Overview")
    
    calendar_events = []
    
    # 1. Plot Tasks
    for index, row in df.iterrows():
        base_date = parse_date_safely(row['last_completed'])
        target_span = get_days_interval(row['frequency'])
        next_due = base_date + timedelta(days=target_span)
        is_overdue = today >= next_due
        event_color = "#FF4B4B" if is_overdue else "#1C83E1"
        
        calendar_events.append({
            "title": f"⚠️ Due: {row['task_name']}" if is_overdue else f"🔄 {row['task_name']}",
            "start": next_due.strftime(STORAGE_DATE_FORMAT),
            "end": next_due.strftime(STORAGE_DATE_FORMAT),
            "backgroundColor": event_color,
            "borderColor": event_color,
            "allDay": True
        })
        
    # 2. Plot Notes
    for index, row in notes_df.iterrows():
        n_date = parse_date_safely(row['event_date']).strftime(STORAGE_DATE_FORMAT)
        calendar_events.append({
            "title": f"📌 {row['title']}",
            "start": n_date,
            "end": n_date,
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
    
    # Render calendar
    calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
