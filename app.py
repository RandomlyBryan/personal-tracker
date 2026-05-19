import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Page Configuration
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
        "task_id": [1, 2],
        "task_name": ["Weekly Tracker Maintenance", "Monthly Budget Check-in"],
        "frequency": ["Weekly", "Monthly"],
        "last_completed": [
            (datetime.now() - timedelta(days=8)).strftime(DATE_FORMAT), 
            (datetime.now() - timedelta(days=32)).strftime(DATE_FORMAT)
        ]
    }
    df = pd.DataFrame(starter_data)
    df.to_csv(DB_FILE, index=False)
else:
    df = pd.read_csv(DB_FILE)

# Helper function to save changes to our file
def save_db(dataframe):
    dataframe.to_csv(DB_FILE, index=False)

# Helper function to fire off notification emails safely
def send_email_notification(task_name, days_overdue):
    try:
        # Pull configuration keys securely from Streamlit's secrets manager
        secret_cfg = st.secrets["email"]
        
        msg = MIMEMultipart()
        msg['From'] = secret_cfg["sender_email"]
        msg['To'] = secret_cfg["receiver_email"]
        msg['Subject'] = f"⏰ Tracker Alert: {task_name} Needs Attention!"
        
        body = f"Hello!\n\nThis is an automated reminder that your task: '{task_name}' requires an update.\nIt was last completed {days_overdue} days ago.\n\nUpdate it here: https://share.streamlit.io/"
        msg.attach(MIMEText(body, 'plain'))
        
        # Open SSL link and authenticate background email transmission
        with smtplib.SMTP_SSL(secret_cfg["smtp_server"], secret_cfg["port"]) as server:
            server.login(secret_cfg["sender_email"], secret_cfg["sender_password"])
            server.sendmail(secret_cfg["sender_email"], secret_cfg["receiver_email"], msg.as_string())
        return True
    except Exception as e:
        # Silently log errors if secrets aren't filled out correctly yet
        return False

# Application UI Header
st.title("🗓️ My Personal Tracker & Scheduler")
st.markdown("---")

# --- PART 2: REMINDERS & ALERTS ---
st.subheader("🔔 Action Required")

today = datetime.now().date()
reminders_found = False

for index, row in df.iterrows():
    last_comp_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
    days_since = (today - last_comp_date).days
    
    is_overdue = False
    if row['frequency'] == "Weekly" and days_since >= 7:
        is_overdue = True
        msg = f"**{row['task_name']}** needs an update! (Last updated {days_since} days ago)"
    elif row['frequency'] == "Monthly" and days_since >= 30:
        is_overdue = True
        msg = f"**{row['task_name']}** requires its monthly check-in! (Last updated {days_since} days ago)"
        
    if is_overdue:
        reminders_found = True
        col_text, col_btn = st.columns([4, 1])
        with col_text:
            st.warning(msg)
            
            # AUTOMATED TRIGGER: If overdue and not mailed yet this session, send notification
            if row['task_id'] not in st.session_state.emails_sent_today:
                if send_email_notification(row['task_name'], days_since):
                    st.session_state.emails_sent_today.append(row['task_id'])
                    st.info(f"📧 Notification alert dispatched to your inbox for '{row['task_name']}'!")
                    
        with col_btn:
            if st.button("Mark Completed", key=f"remind_btn_{row['task_id']}"):
                df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                save_db(df)
                # Clear session email cache for this item upon successful check-in
                if row['task_id'] in st.session_state.emails_sent_today:
                    st.session_state.emails_sent_today.remove(row['task_id'])
                st.rerun()

if not reminders_found:
    st.success("All clear! Your recurring tasks are up to date.")

st.markdown("---")

# --- PART 3: MASTER SCHEDULE INTERFACE (WITH EDIT/DELETE) ---
st.subheader("📋 Master Schedule Overview")

if df.empty:
    st.info("Your schedule is currently empty. Add a task below to get started!")
else:
    hdr_col1, hdr_col2, hdr_col3, hdr_col4, hdr_col5 = st.columns([3, 1, 1, 1, 1])
    hdr_col1.markdown("**Task Name**")
    hdr_col2.markdown("**Frequency**")
    hdr_col3.markdown("**Last Completed**")
    hdr_col4.markdown("**Next Due Date**")
    hdr_col5.markdown("**Actions**")
    st.markdown("---")

    for index, row in df.iterrows():
        base_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
        next_due = base_date + timedelta(days=7) if row['frequency'] == "Weekly" else base_date + timedelta(days=30)
        
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        if st.session_state.editing_task_id == row['task_id']:
            with col1:
                edit_name = st.text_input("Edit Name", value=row['task_name'], label_visibility="collapsed", key=f"edit_name_{row['task_id']}")
            with col2:
                edit_freq = st.selectbox("Edit Freq", ["Weekly", "Monthly"], index=0 if row['frequency'] == "Weekly" else 1, label_visibility="collapsed", key=f"edit_freq_{row['task_id']}")
            with col3:
                st.write(row['last_completed'])
            with col4:
                st.write(next_due.strftime(DATE_FORMAT))
            with col5:
                btn_save, btn_cancel = st.columns(2)
                with btn_save:
                    if st.button("💾", key=f"save_{row['task_id']}"):
                        df.at[index, 'task_name'] = edit_name
                        df.at[index, 'frequency'] = edit_freq
                        save_db(df)
                        st.session_state.editing_task_id = None
                        st.rerun()
                with btn_cancel:
                    if st.button("❌", key=f"cancel_{row['task_id']}"):
                        st.session_state.editing_task_id = None
                        st.rerun()
        else:
            with col1:
                st.write(row['task_name'])
            with col2:
                st.write(row['frequency'])
            with col3:
                st.write(row['last_completed'])
            with col4:
                st.write(next_due.strftime(DATE_FORMAT))
            with col5:
                btn_edit, btn_delete = st.columns(2)
                with btn_edit:
                    if st.button("✏️", key=f"edit_mode_{row['task_id']}"):
                        st.session_state.editing_task_id = row['task_id']
                        st.rerun()
                with btn_delete:
                    if st.button("🗑️", key=f"delete_{row['task_id']}"):
                        df = df[df['task_id'] != row['task_id']]
                        save_db(df)
                        st.rerun()
        
        st.markdown("<hr style='margin:0.2em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

# --- PART 4: CREATE NEW ITEMS ---
st.markdown("---")
st.subheader("➕ Add Custom Recurring Task")

with st.form("new_task_form", clear_on_submit=True):
    new_name = st.text_input("Task Description")
    new_freq = st.selectbox("Interval Cycle", ["Weekly", "Monthly"])
    submitted = st.form_submit_button("Create Entry")
    
    if submitted and new_name:
        new_id = int(df['task_id'].max() + 1) if not df.empty else 1
        default_past = today - timedelta(days=8 if new_freq == "Weekly" else 32)
        
        new_row = {
            "task_id": new_id,
            "task_name": new_name,
            "frequency": new_freq,
            "last_completed": default_past.strftime(DATE_FORMAT)
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_db(df)
        st.success(f"Successfully added: {new_name}")
        st.rerun()
