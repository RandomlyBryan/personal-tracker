import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar
import streamlit.components.v1 as components  # Required for HTML/JS injection

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
PRIORITIES_FILE = "next_day_priorities.csv" 
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
        df.to_csv(DB_FILE, index=False)
    # Ensure NaN data spaces are filled cleanly as text to protect edit tasks
    df["task_url"] = df["task_url"].fillna("").astype(str)

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

if not os.path.exists(PRIORITIES_FILE):
    prio_df = pd.DataFrame(columns=["prio_id", "item_text"])
    prio_df.to_csv(PRIORITIES_FILE, index=False)
else:
    prio_df = pd.read_csv(PRIORITIES_FILE)

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

def send_email_notification(task_name, days_overdue, description, resource_url):
    try:
        secret_cfg = st.secrets["email"]
        msg = MIMEMultipart()
        msg['From'] = secret_cfg["sender_email"]
        msg['To'] = secret_cfg["receiver_email"]
        msg['Subject'] = f"⏰ Routine Reminder: {task_name} is Overdue!"
        link_line = f"🔗 Resource Link: {resource_url}\n" if resource_url and str(resource_url) != "nan" and str(resource_url).strip() != "" else ""
        body = (
            f"Hello Bryan,\n\n"
            f"This is an automated alert from your Personal Tracker Dashboard.\n"
            f"The following routine requires an update:\n\n"
            f"📌 Task: {task_name} ({days_overdue} days since last update)\n"
            f"📝 Instructions:\n{description}\n"
            f"{link_line}\n"
            f"Access your live control panel to mark this complete: https://share.streamlit.io/"
        )
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL(secret_cfg["smtp_server"], secret_cfg["port"]) as server:
            server.login(secret_cfg["sender_email"], secret_cfg["sender_password"])
            server.sendmail(secret_cfg["sender_email"], secret_cfg["receiver_email"], msg.as_string())
        return True
    except Exception as e:
        return False

# Centered main screen title
st.markdown(
    "<h1 style='text-align: center; font-family: Georgia, serif;'>🗓️ Personal Tracker Dashboard</h1>", 
    unsafe_allow_html=True
)
st.markdown("---")

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

# --- CALCULATE OVERDUE TASKS FOR PUSH ALERTS ---
overdue_tasks_list = []
for _, row in df.iterrows():
    last_comp_date = parse_date_safely(row['last_completed'])
    if (today - last_comp_date).days >= get_days_interval(row['frequency']):
        overdue_tasks_list.append(row['task_name'])

# If overdue items exist, render native browser notifications engine
if overdue_tasks_list:
    alert_summary = f"You have {len(overdue_tasks_list)} items requiring update: " + ", ".join(overdue_tasks_list[:2])
    if len(overdue_tasks_list) > 2:
        alert_summary += f" and {len(overdue_tasks_list) - 2} more."

    js_notification_code = f"""
    <script>
    function triggerDesktopPush() {{
        if (!("Notification" in window)) {{
            console.log("Browser does not support notifications.");
            return;
        }}
        if (Notification.permission === "granted") {{
            new Notification("⏰ Overdue Routines Alert", {{
                body: "{alert_summary}",
                icon: "https://cdn-icons-png.flaticon.com/512/599/599502.png"
            }});
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission().then(function (permission) {{
                if (permission === "granted") {{
                    new Notification("⏰ Overdue Routines Alert", {{
                        body: "{alert_summary}",
                        icon: "https://cdn-icons-png.flaticon.com/512/599/599502.png"
                    }});
                }}
            }});
        }}
    }}
    setTimeout(triggerDesktopPush, 1000);
    </script>
    """
    components.html(js_notification_code, height=0, width=0)

# Side-by-side split layout
left_panel, right_panel = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT PANEL: COMPACT TABBED WORKSPACE WITH AUTOMATED EOD ENGINE
# ------------------------------------------
with left_panel:
    st.header("📋 Command Center")
    
    tab_alerts, tab_eod, tab_add, tab_manage = st.tabs(["🚨 Pending Tasks", "📝 EOD Report", "➕ New Task", "⚙️ Existing Task"])
    
    # --- TAB 1: PENDING TASKS & ALERTS ---
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
                    
                    if row['task_id'] not in st.session_state.emails_sent_today:
                        t_desc = row['task_description'] if pd.notna(row['task_description']) else "No instructions provided."
                        t_url = row['task_url'] if pd.notna(row['task_url']) else ""
                        if send_email_notification(row['task_name'], days_since, t_desc, t_url):
                            st.session_state.emails_sent_today.append(row['task_id'])
                            st.info(f"📧 Notification dispatched for '{row['task_name']}'!")
                            
                with col_btn:
                    if st.button("Done", key=f"remind_btn_{row['task_id']}"):
                        df.at[index, 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                        save_db(df, DB_FILE)
                        
                        new_log_id = int(eod_df['log_id'].max() +
