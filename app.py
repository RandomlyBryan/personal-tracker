import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Page Configuration (Wide mode is essential for side-by-side)
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database File Setup
DB_FILE = "tasks_db.csv"
DATE_FORMAT = "%d/%m/%Y"

# Initialize temporary memory states
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

# Load existing tasks or initialize defaults
if not os.path.exists(DB_FILE):
    starter_data = {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup & Coding Check-in", "Weekly Tracker Maintenance", "Monthly Budget Check-in"],
        "task_description": [
            "Review yesterdays work and map out what to code next.",
            "1. Check app for typos.\n2. Verify database values on GitHub.",
            "1. Open online banking.\n2. Export statements to spreadsheet."
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
    if "task_description" not in df.columns:
        df["task_description"] = "No instructions provided yet."

# Helper function to save changes to our file
def save_db(dataframe):
    dataframe.to_csv(DB_FILE, index=False)

# Helper function to fire off notification emails safely
def send_email_notification(task_name, days_overdue, description):
    try:
        secret_cfg = st.secrets["email"]
        msg = MIMEMultipart()
        msg['From'] = secret_cfg["sender_email"]
        msg['To'] = secret_cfg["receiver_email"]
        msg['Subject'] = f"⏰ Tracker Alert: {task_name} Needs Attention!"
        
        body = f"Hello!\n\nThis is an automated reminder that your task: '{task_name}' requires an update.\nIt was last completed {days_overdue} days ago.\n\n📝 Instructions:\n{description}\n\nUpdate it here: https://share.streamlit.io/"
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL(secret_cfg["smtp_server"], secret_cfg["port"]) as server:
            server.login(secret_cfg["sender_email"], secret_cfg["sender_password"])
            server.sendmail(secret_cfg["sender_email"], secret_cfg["receiver_email"], msg.as_string())
        return True
    except:
        return False

# Application UI Header
st.title("🗓️ Personal Tracker Dashboard")
st.markdown("---")

# Helper to map frequencies to numeric intervals
def get_days_interval(freq_string):
    if freq_string == "Daily":
        return 1
    elif freq_string == "Weekly":
        return 7
    else:
        return 30

today = datetime.now().date()

# ==========================================
# SPLIT INTERFACE INTO TWO SIDE-BY-SIDE PANELS
# ==========================================
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: ACTIVE TASKS, REMINDERS & BUILDER
# ------------------------------------------
with left_panel:
    st.header("📋 Task & Routine Manager")
    
    # --- Reminders Sub-section ---
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
                
                # Background email trigger
                if row['task_id'] not in st.session_state.emails_sent_today:
                    if send_email_notification(row['task_name'], days_since, row['task_description']):
                        st.session_state.emails_sent_today.append(row['task_id'])
                        st.info("📧 Alert email dispatched.")
            with col_btn:
                if st.button("Complete", key=f"remind_btn_{row['task_id']}"):
                    df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                    save_db(df)
                    if row['task_id'] in st.session_state.emails_sent_today:
                        st.session_state.emails_sent_today.remove(row['task_id'])
                    st.rerun()
                    
    if not reminders_found:
        st.success("🎉 All routines are current and up to date!")
        
    st.markdown("---")
    
    # --- Edit / Delete Schedule list ---
    st.subheader("⚙️ Edit Schedule Items")
    
    for index, row in df.iterrows():
        # Layout individual edit records
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
                if st.button("❌", key=f"c_{row['task_id']}"):
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
    
    # --- Creation Engine ---
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
# RIGHT PANEL: VISUAL SCHEDULE CALENDAR GRID
# ------------------------------------------
with right_panel:
    st.header("📅 Visual Schedule & Agenda")
    
    # Format and process calendar calculations map
    cal_events = []
    for index, row in df.iterrows():
        base_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
        target_span = get_days_interval(row['frequency'])
        next_due = base_date + timedelta(days=target_span)
        
        cal_events.append({
            "Task": row['task_name'],
            "Frequency": row['frequency'],
            "Last Updated": base_date.strftime(DATE_FORMAT),
            "Next Due Date": next_due.strftime(DATE_FORMAT),
            "Status": "⚠️ Overdue" if today >= next_due else "✅ OK"
        })
        
    cal_df = pd.DataFrame(cal_events)
    
    if not cal_df.empty:
        # Render high-visibility metrics for dates
        st.subheader("Next Upcoming Targets")
        st.dataframe(cal_df, use_container_width=True, hide_index=True)
        
        # Display simple agenda breakdown timeline
        st.subheader("Timeline Agenda Tracker")
        for event in cal_events:
            status_color = "🔴" if event["Status"] == "⚠️ Overdue" else "🟢"
            st.info(f"{status_color} **{event['Next Due Date']}** — {event['Task']} ({event['Frequency']})")
    else:
        st.info("No items scheduled to build out calendar dates.")
