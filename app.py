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
        
        /* CLEAN INLINE QUICK COPY CONTAINERS */
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
        
        /* SUMMARY CODE MODULES */
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
            
        payload = {
            "message": f"🤖 Automated Dashboard Sync: Update {filename}",
            "content": encoded_content,
            "branch": branch
        }
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception:
        pass

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

# Fail-safe initialization to verify size of file handles to avoid EmptyDataError crashes
if not os.path.exists(EOD_FILE) or os.path.getsize(EOD_FILE) == 0:
    eod_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS)
    eod_df.to_csv(EOD_FILE, index=False)
    push_to_github(EOD_FILE)
else:
    eod_df = pd.read_csv(EOD_FILE)
    eod_df = verify_and_align_columns(eod_df, EOD_FILE, REQUIRED_LOG_COLUMNS)

# FIX: Added an extra size protection validation check on the archive file to fix the crash
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

def send_email_notification(task_name, days_overdue, description, resource_url):
    try:
        secret_cfg = st.secrets["email"]
        msg = MIMEMultipart()
        msg['From'] = secret_cfg["sender_email"]
        msg['To'] = secret_cfg["receiver_email"]
        msg['Subject'] = f"⏰ Routine Reminder: {task_name} is Overdue!"
        link_line = f"🔗 Resource Link: {resource_url}\n" if resource_url and str(resource_url) != "nan" and str(resource_url).strip() != "" else ""
        body = (f"Hello Bryan,\n\nThis is an automated alert from your Personal Tracker Dashboard.\nThe following routine requires an update:\n\n📌 Task: {task_name}\n📝 Instructions:\n{description}\n{link_line}\nAccess control panel: https://share.streamlit.io/")
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL(secret_cfg["smtp_server"], secret_cfg["port"]) as server:
            server.login(secret_cfg["sender_email"], secret_cfg["sender_password"])
            server.sendmail(secret_cfg["sender_email"], secret_cfg["receiver_email"], msg.as_string())
        return True
    except Exception: return False

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

# --- ALERTS MANAGEMENT ---
overdue_tasks_list = []
for _, row in df.iterrows():
    loop_comp_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
    if (today - loop_comp_date).days >= get_days_interval(row.get('frequency', 'Daily')):
        overdue_tasks_list.append(row.get('task_name', 'Unknown Task'))

if overdue_tasks_list:
    alert_summary = f"You have {len(overdue_tasks_list)} items requiring update: " + ", ".join(overdue_tasks_list[:2])
    if len(overdue_tasks_list) > 2: alert_summary += f" and {len(overdue_tasks_list) - 2} more."
    js_notification_code = f"<script>setTimeout(function(){{ if(Notification.permission==='granted'){{ new Notification('⏰ Overdue Routines Alert', {{ body: '{alert_summary}' }}); }} }}, 1000);</script>"
    components.html(js_notification_code, height=0, width=0)

main_layout_frame, right_buffer_column = st.columns([12, 1])

with main_layout_frame:
    # --- SECTION 1: MONTHLY OVERVIEW ---
    st.header("📅 Monthly Overview")
    calendar_events = []
    for index, row in df.iterrows():
        base_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
        next_due = base_date + timedelta(days=get_days_interval(row.get('frequency', 'Daily')))
        is_overdue = today >= next_due
        
        calendar_display_date = today if is_overdue else next_due
        event_color = "#EF4444" if is_overdue else "#1E3A8A"
        formatted_cal_date = calendar_display_date.strftime(STORAGE_DATE_FORMAT)
        
        calendar_events.append({
            "title": f"⚠️ Due: {row.get('task_name', 'Task')}" if is_overdue else f"{'📌' if str(row.get('is_recurring', 'Yes')) == 'No' else '🔄'} {row.get('task_name', 'Task')}", 
            "start": formatted_cal_date, 
            "end": formatted_cal_date, 
            "backgroundColor": event_color, 
            "borderColor": event_color, 
            "allDay": True
        })
    for index, row in notes_df.iterrows():
        n_date = parse_date_safely(row['event_date']).strftime(STORAGE_DATE_FORMAT)
        calendar_events.append({"title": f"📌 {row['title']}", "start": n_date, "end": n_date, "backgroundColor": "#334155", "borderColor": "#334155", "allDay": True})
    calendar(events=calendar_events, options={"initialView": "dayGridMonth", "headerToolbar": { "left": "prev,next today", "center": "title", "right": "" }, "editable": False, "selectable": True, "height": "auto", "dayMaxEvents": True, "moreLinkClick": "popover"}, key="monthly_grid_view")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Performance Analytics & Velocity Insights", expanded=False):
        if not archive_df.empty:
            archive_df['parsed_date'] = archive_df['log_date'].apply(parse_date_safely)
            total_tasks_completed = len(archive_df)
            seven_days_ago = today - timedelta(days=7)
            recent_week_df = archive_df[archive_df['parsed_date'] >= seven_days_ago]
            week_completions_count = len(recent_week_df)
            
            m_col1, m_col2 = st.columns(2)
            with m_col1: st.metric(label="Total Archived Tasks Closed", value=total_tasks_completed)
            with m_col2: st.metric(label="Tasks Closed (Past 7 Days)", value=week_completions_count)
                
            st.markdown("**Daily Production Velocity Profile:**")
            chart_data = archive_df.groupby('log_date').size().reset_index(name='Tasks Completed')
            chart_data = chart_data.sort_values(by='log_date').tail(10)
            chart_data = chart_data.set_index('log_date')
            st.bar_chart(chart_data, color="#38BDF8")
        else:
            st.info("Analytics metrics will populate automatically here as actions are moved into the history archives.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECTION 2: COMMAND CENTER TABS ---
    st.header("📋 Command Center")
    
    tab_alerts, tab_add, tab_manage, tab_eod, tab_archive = st.tabs([
        "🚨 Pending Tasks", 
        "➕ New Task", 
        "⚙️ Existing Task",
        "📝 EOD Report", 
        "📊 Task History"
    ])
    
    # --- TAB 1: PENDING TASKS ---
    with tab_alerts:
        st.subheader("Pending Tasks")
        
        active_pending_df = df.copy()
        if "task_priority" in active_pending_df.columns:
            active_pending_df["task_priority"] = pd.to_numeric(active_pending_df["task_priority"]).fillna(3).astype(int)
            active_pending_df = active_pending_df.sort_values(by="task_priority", ascending=False)
        
        reminders_found = False
        for index, row in active_pending_df.iterrows():
            last_comp_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
            days_since = (today - last_comp_date).days
            if days_since >= get_days_interval(row.get('frequency', 'Daily')):
                reminders_found = True
                
                star_weight = int(row.get('task_priority', 3))
                star_render_string = "⭐" * star_weight
                
                type_label = "📌 One-Time" if str(row.get('is_recurring', 'Yes')) == "No" else "🔄 Recurring"
                st.markdown(f"### **{row.get('task_name', 'Unnamed Task')}** <span class='stars-container'>{star_render_string}</span>", unsafe_allow_html=True)
                st.caption(f"Cycle: {row.get('frequency', 'Daily')} — *{type_label}*")
                
                desc_content = str(row.get('task_description', 'No instructions.'))
                lines = desc_content.split("\n")
                has_excel_formulas = any(line.strip().startswith("=") for line in lines)
                
                if has_excel_formulas:
                    yes_formulas = []
                    no_formulas = []
                    plain_instructions = []
                    
                    current_bucket = None
                    for line in lines:
                        cleaned_line = line.strip()
                        if not cleaned_line: continue
                        if cleaned_line.lower() == "yes": current_bucket = "yes"
                        elif cleaned_line.lower() == "no": current_bucket = "no"
                        elif cleaned_line.startswith("="):
                            if current_bucket == "yes": yes_formulas.append(cleaned_line)
                            elif current_bucket == "no": no_formulas.append(cleaned_line)
                            else: plain_instructions.append(cleaned_line)
                        else:
                            if cleaned_line.lower() not in ["formula to use:", "formula to use"]: plain_instructions.append(cleaned_line)
                    
                    for inst in plain_instructions:
                        st.markdown(f"**{inst}**")
                    
                    st.markdown("#### **📋 Formula Shortcut Guide:**")
                    grid_col_left, grid_col_right = st.columns(2, gap="medium")
                    
                    with grid_col_left:
                        st.markdown("<span style='color:#38BDF8; font-weight:bold;'>🟢 'Yes' Counters:</span>", unsafe_allow_html=True)
                        if yes_formulas:
                            for f_item in yes_formulas:
                                st.markdown("<div class='clean-copy'>", unsafe_allow_html=True)
                                st.code(f_item, language=None)
                                st.markdown("</div>", unsafe_allow_html=True)
                        else: st.caption("None configured.")
                            
                    with grid_col_right:
                        st.markdown("<span style='color:#94A3B8; font-weight:bold;'>🔴 'No' Counters:</span>", unsafe_allow_html=True)
                        if no_formulas:
                            for f_item in no_formulas:
                                st.markdown("<div class='clean-copy'>", unsafe_allow_html=True)
                                st.code(f_item, language=None)
                                st.markdown("</div>", unsafe_allow_html=True)
                        else: st.caption("None configured.")
                else:
                    st.write(desc_content)
                    
                saved_links_str = str(row.get('task_url', '')).strip()
                if saved_links_str and saved_links_str != "nan":
                    link_cols = st.columns(min(max(len(saved_links_str.split(",")), 1), 4))
                    for idx, url_item in enumerate(saved_links_str.split(",")):
                        if url_item.strip():
                            with link_cols[idx % 4]:
                                st.link_button(f"🔗 Open Reference Link", url=url_item.strip(), use_container_width=True)
                
                saved_img_b64 = str(row.get('task_screenshot_b64', '')).strip()
                if saved_img_b64 and saved_img_b64 != "nan":
                    try: st.image(base64.b64decode(saved_img_b64), caption="Reference Screenshot", width=350)
                    except Exception: pass
                
                st.markdown("<div class='pending-row-form'>", unsafe_allow_html=True)
                with st.form(key=f"form_pending_{row.get('task_id')}"):
                    result_notes = st.text_area(
                        label="Action Notes / Results Summary:",
                        placeholder="Type verification updates here...",
                        key=f"res_{row.get('task_id')}",
                        height=68
                    )
                    
                    uploaded_doc_file = st.file_uploader(
                        "📎 Attach Deliverable Document (Optional - Excel, Word, PDF, or Sheet Exports):",
                        type=["xlsx", "xls", "docx", "doc", "pdf", "csv"],
                        key=f"doc_attach_{row.get('task_id')}"
                    )
                    
                    submit_trigger = st.form_submit_button("Done")
                    if submit_trigger:
                        clean_notes = result_notes.strip() if result_notes.strip() else "Completed successfully."
                        
                        encoded_doc_b64 = ""
                        doc_name_label = ""
                        if uploaded_doc_file is not None:
                            encoded_doc_b64 = base64.b64encode(uploaded_doc_file.read()).decode('utf-8')
                            doc_name_label = uploaded_doc_file.name
                            
                        new_log_id = int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1
                        new_log_row = {
                            "log_id": new_log_id, 
                            "task_title": str(row.get('task_name', 'Manual Log')).strip(), 
                            "bullet_text": clean_notes, 
                            "log_date": today.strftime(STORAGE_DATE_FORMAT), 
                            "task_links": str(row.get('task_url', '')), 
                            "screenshot_b64": str(row.get('task_screenshot_b64', '')),
                            "doc_attachment_b64": encoded_doc_b64,
                            "doc_attachment_name": doc_name_label
                        }
                        eod_df = pd.concat([eod_df, pd.DataFrame([new_log_row])], ignore_index=True)
                        save_and_push(eod_df, EOD_FILE)
                        
                        orig_idx = df[df['task_id'] == row.get('task_id')].index
                        if not orig_idx.empty:
                            if str(row.get('is_recurring', 'Yes')) == "No": df = df.drop(orig_idx)
                            else: df.at[orig_idx[0], 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                            save_and_push(df, DB_FILE)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:1.5em 0px; border-color:#232936;'>", unsafe_allow_html=True)
        if not reminders_found: st.success("🎉 Everything is running on schedule!")

    # --- TAB 2: NEW TASK ---
    with tab_add:
        sub_tab_task, sub_tab_note = st.tabs(["🔄 Recurring Routine", "📌 One-Time Note"])
        with sub_tab_task:
            with st.form("new_task_form", clear_on_submit=True):
                new_name = st.text_input("Task Title")
                new_desc = st.text_area("Instructions & Specific Formulas (Place each formula on its own line starting with '=')")
                bulk_urls_input = st.text_area("Task Resource URLs (Paste one URL per line):", placeholder="https://example1.com\nhttps://example2.com")
                uploaded_task_media = st.file_uploader("Attach Base Reference Screenshot (Optional):", type=["png", "jpg", "jpeg"])
                
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1: new_freq = st.selectbox("Interval Cycle", ["Daily", "Weekly", "Monthly"])
                with col_f2: recurrence_setting = st.selectbox("Is this task recurring?", ["Yes", "No"])
                with col_f3: selected_star_lbl = st.selectbox("Assign Priority Star Level:", STAR_OPTIONS, index=2)
                
                start_date = st.date_input("Routine Start Date", value=today)
                if st.form_submit_button("Save Routine") and new_name:
                    comma_links = ",".join([l.strip() for l in bulk_urls_input.split("\n") if l.strip()]) if bulk_urls_input.strip() else ""
                    media_b64 = base64.b64encode(uploaded_task_media.read()).decode('utf-8') if uploaded_task_media is not None else ""
                    new_id = int(df['task_id'].max() + 1) if not df.empty else 1
                    
                    numeric_prio_weight = STAR_OPTIONS.index(selected_star_lbl) + 1
                    
                    new_task_row = {
                        "task_id": new_id, 
                        "task_name": new_name, 
                        "task_description": new_desc if new_desc else "No instructions.", 
                        "task_url": comma_links, 
                        "frequency": new_freq, 
                        "is_recurring": recurrence_setting, 
                        "last_completed": start_date.strftime(STORAGE_DATE_FORMAT), 
                        "task_screenshot_b64": media_b64,
                        "task_priority": numeric_prio_weight
                    }
                    df = pd.concat([df, pd.DataFrame([new_task_row])], ignore_index=True)
                    save_and_push(df, DB_FILE)
                    st.rerun()
                    
        with sub_tab_note:
            with st.form("new_note_form", clear_on_submit=True):
                note_title = st.text_input("Meeting / Event Title")
                note_details = st.text_area("Agenda Notes")
                note_date = st.date_input("Event Date", value=today)
                if st.form_submit_button("Pin to Calendar") and note_title:
                    new_note_id = int(notes_df['note_id'].max() + 1) if not notes_df.empty else 1
                    notes_df = pd.concat([notes_df, pd.DataFrame([{"new_note_id": new_note_id, "title": note_title, "details": note_details if note_details else "", "event_date": note_date.strftime(STORAGE_DATE_FORMAT)}])], ignore_index=True)
                    save_and_push(notes_df, NOTES_FILE)
                    st.rerun()

    # --- TAB 3: EXISTING TASK ---
    with tab_manage:
        st.subheader("Edit & Delete Settings")
        m_task, m_note, m_danger = st.tabs(["Rotations", "Calendar Notes", "⚠️ Factory Reset"])
        with m_task:
            maintenance_df = df.copy()
            if "task_priority" in maintenance_df.columns:
                maintenance_df["task_priority"] = pd.to_numeric(maintenance_df["task_priority"]).fillna(3).astype(int)
                maintenance_df = maintenance_df.sort_values(by="task_priority", ascending=False)
                
            for index, row in maintenance_df.iterrows():
                ec1, ec2, ec3 = st.columns([2.5, 1.5, 1.0])
                current_task_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
                orig_master_idx = df[df['task_id'] == row.get('task_id')].index[0]
                
                if st.session_state.editing_task_id == row.get('task_id'):
                    with ec1:
                        edit_name = st.text_input("Name", value=row.get('task_name', ''), key=f"en_{row.get('task_id')}", label_visibility="collapsed")
                        edit_desc = st.text_area("Desc", value=row.get('task_description', ''), key=f"ed_{row.get('task_id')}", label_visibility="collapsed")
                        edit_url = st.text_input("URL Link", value=str(row.get('task_url', '')), key=f"eurl_{row.get('task_id')}")
                    with ec2:
                        edit_freq = st.selectbox("Freq", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row.get('frequency', 'Daily')), key=f"ef_{row.get('task_id')}", label_visibility="collapsed")
                        edit_rec = st.selectbox("Recurring?", ["Yes", "No"], index=["Yes", "No"].index(str(row.get('is_recurring', 'Yes')) if str(row.get('is_recurring', 'Yes')) in ["Yes", "No"] else "Yes"), key=f"erec_{row.get('task_id')}", label_visibility="collapsed")
                        current_prio_val = int(row.get('task_priority', 3))
                        fallback_prio_idx = (current_prio_val - 1) if 1 <= current_prio_val <= 5 else 2
                        edit_star_lbl = st.selectbox("Edit Star Priority Level", STAR_OPTIONS, index=fallback_prio_idx, key=f"eprio_{row.get('task_id')}")
                        edit_t_date = st.date_input("Edit Start Date", value=current_task_date, key=f"etd_{row.get('task_id')}", label_visibility="collapsed")
                    with ec3:
                        if st.button("💾", key=f"s_{row.get('task_id')}"):
                            df.at[orig_master_idx, 'task_name'] = edit_name
                            df.at[orig_master_idx, 'task_description'] = edit_desc
                            df.at[orig_master_idx, 'task_url'] = edit_url.strip()
                            df.at[orig_master_idx, 'frequency'] = edit_freq
                            df.at[orig_master_idx, 'is_recurring'] = edit_rec
                            df.at[orig_master_idx, 'last_completed'] = edit_t_date.strftime(STORAGE_DATE_FORMAT)
                            df.at[orig_master_idx, 'task_priority'] = STAR_OPTIONS.index(edit_star_lbl) + 1
                            
                            save_and_push(df, DB_FILE)
                            st.session_state.editing_task_id = None
                            st.rerun()
                else:
                    with ec1:
                        current_stars_count = int(row.get('task_priority', 3))
                        star_display = "⭐" * current_stars_count
                        st.write(f"**{row.get('task_name', 'Task')}** — <span class='stars-container'>{star_display}</span>", unsafe_allow_html=True)
                        st.caption(f"Cycle: {row.get('frequency', 'Daily')} — *{'One-Time' if str(row.get('is_recurring', 'Yes')) == 'No' else 'Recurring'}*")
                        if str(row.get('task_url', '')).strip() and str(row.get('task_url', '')) != "nan": st.caption("🔗 Link Data Saved")
                    with ec2:
                        if st.button("✏️", key=f"em_{row.get('task_id')}"): st.session_state.editing_task_id = row.get('task_id'); st.rerun()
                    with ec3:
                        if st.button("🗑️", key=f"d_{row.get('task_id')}"): 
                            df = df.drop(orig_master_idx)
                            save_and_push(df, DB_FILE)
                            st.rerun()
                st.markdown("<hr style='margin:0.05em 0px; border-color:#232936;'>", unsafe_allow_html=True)
                
        with m_note:
            if notes_df.empty: st.info("No temporary calendar notes pinned.")
            else:
                for index, row in notes_df.iterrows():
                    nc1, nc2, nc3 = st.columns([3, 1, 1])
                    if st.session_state.editing_note_id == row['note_id']:
                        with nc1:
                            en_title = st.text_input("Title", value=row['title'], key=f"ent_{row['note_id']}", label_visibility="collapsed")
                            en_details = st.text_area("Details", value=row['details'], key=f"end_{row['note_id']}", label_visibility="collapsed")
                        with nc2: en_date = st.date_input("Date", value=parse_date_safely(row['event_date']), key=f"endate_{row['note_id']}", label_visibility="collapsed")
                        with nc3:
                            if st.button("💾", key=f"s_note_{row['note_id']}"):
                                notes_df.at[index, 'title'] = en_title; notes_df.at[index, 'details'] = en_details; notes_df.at[index, 'event_date'] = en_date.strftime(STORAGE_DATE_FORMAT)
                                save_and_push(notes_df, NOTES_FILE); st.session_state.editing_note_id = None; st.rerun()
                    else:
                        with nc1:
                            st.write(f"📌 **{parse_date_safely(row['event_date']).strftime(DATE_FORMAT)}** — {row['title']}")
                            if row['details']:
                                with st.expander("📄 View Details"): st.write(row['details'])
                        with nc2:
                            if st.button("✏️", key=f"em_note_{row['note_id']}"): st.session_state.editing_note_id = row['note_id']; st.rerun()
                        with nc3:
                            if st.button("🗑️", key=f"del_note_{row['note_id']}"): notes_df = notes_df[notes_df['note_id'] != row['note_id']]; save_and_push(notes_df, NOTES_FILE); st.rerun()
                    st.markdown("<hr style='margin:0.05em 0px; border-color:#232936;'>", unsafe_allow_html=True)
        with m_danger:
            st.markdown("<span style='color:#EF4444; font-weight:bold;'>🚨 CRITICAL ZONE: Factory Reset</span>", unsafe_allow_html=True)
            if st.text_input("Type RESET ALL to unlock confirmation:", placeholder="RESET ALL") == "RESET ALL":
                if st.button("💥 WIPE REPOSITORIES", use_container_width=True):
                    df = pd.DataFrame(get_starter_tasks()); save_and_push(df, DB_FILE)
                    for target_csv in [NOTES_FILE, EOD_FILE, PRIORITIES_FILE, ARCHIVE_FILE]:
                        if os.path.exists(target_csv): os.remove(target_csv)
                    st.session_state.editing_task_id, st.session_state.editing_note_id, st.session_state.emails_sent_today = None, None, []
                    st.rerun()

    # --- TAB 4: EOD REPORT LOG BUILDER ---
    with tab_eod:
        st.subheader("Daily Task Report")
        st.markdown("**📋 Quick Copy**")
        
        st.markdown("<div class='clean-copy'>", unsafe_allow_html=True)
        st.code("Bryan Reyes", language=None)
        st.code("work.bryanc@gmail.com", language=None)
        st.code("Marketing & Reporting VA", language=None)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        eod_log_col, prio_log_col = st.columns(2)
        with eod_log_col:
            st.markdown("**Add Completed Tasks Manually:**")
            with st.form("eod_add_form", clear_on_submit=True):
                manual_title = st.text_input("Project / Task Title:", value="Manual Log")
                log_input = st.text_input("Action Detail / Note:")
                if st.form_submit_button("Add") and log_input:
                    new_log_id = int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1
                    eod_df = pd.concat([eod_df, pd.DataFrame([{"log_id": new_log_id, "task_title": manual_title.strip() if manual_title.strip() else "Manual Log", "bullet_text": log_input.strip(), "log_date": today.strftime(STORAGE_DATE_FORMAT), "task_links": "", "screenshot_b64": "", "doc_attachment_b64": "", "doc_attachment_name": ""}])], ignore_index=True)
                    save_and_push(eod_df, EOD_FILE)
                    st.rerun()
        with prio_log_col:
            st.markdown("**Next Day Task Priorities:**")
            with st.form("prio_add_form", clear_on_submit=True):
                prio_input = st.text_input("Item for tomorrow:", key="prio_in")
                if st.form_submit_button("Add") and prio_input:
                    new_prio_id = int(prio_df['prio_id'].max() + 1) if not prio_df.empty else 1
                    prio_df = pd.concat([prio_df, pd.DataFrame([{"prio_id": new_prio_id, "item_text": prio_input.strip()}])], ignore_index=True)
                    save_and_push(prio_df, PRIORITIES_FILE)
                    st.rerun()

        st.markdown("---")
        emp_header = f"Date: {today.strftime(DATE_FORMAT)}\n----------------------------------------\nCompleted Tasks & Actions Log:\n"
        if not eod_df.empty:
            grouped_lines = []
            seen_titles = {}
            for _, row in eod_df.iterrows():
                title = row['task_title']
                if title not in seen_titles: seen_titles[title] = []
                seen_titles[title].append(row['bullet_text'])
            for title, entries in seen_titles.items():
                if title == "Manual Log":
                    for note in entries: grouped_lines.append(f"• {note}")
                else:
                    grouped_lines.append(f"• {title}:")
                    for note in entries: grouped_lines.append(f"  - {note}")
            compiled_report = f"{emp_header}" + "\n".join(grouped_lines)
        else: compiled_report = f"{emp_header}• (No work logged yet today.)"
            
        st.markdown("**EOD Summary Block:**")
        st.markdown("<div class='clean-report-block'>", unsafe_allow_html=True)
        st.code(compiled_report, language=None)
        st.markdown("</div>", unsafe_allow_html=True)
        
        has_images_today = False
        for _, row in eod_df.iterrows():
            if str(row.get('screenshot_b64', '')).strip():
                if not has_images_today:
                    st.markdown("**📸 Staged Screenshots Attached Today:**")
                    has_images_today = True
                try: st.image(base64.b64decode(row['screenshot_b64']), caption=f"Screenshot for: {row['task_title']}", width=250)
                except Exception: pass

        auto_priorities = []
        for _, row in df.iterrows():
            l_completed = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
            n_due = l_completed + timedelta(days=get_days_interval(row.get('frequency', 'Daily')))
            if (today - l_completed).days >= get_days_interval(row.get('frequency', 'Daily')): 
                auto_priorities.append(f"• {row.get('task_name', 'Task')}")
            elif n_due == tomorrow: 
                auto_priorities.append(f"• {row.get('task_name', 'Task')}")
                
        for _, row in prio_df.iterrows(): 
            auto_priorities.append(f"• {row['item_text']}")
            
        compiled_prio_report = f"Next Day Priorities / Agenda ({tomorrow.strftime(DATE_FORMAT)}):\n----------------------------------------\n" + ("\n".join(auto_priorities) if auto_priorities else "• No priorities scheduled for tomorrow.")
        
        st.markdown("**Next Day Priorities:**")
        st.markdown("<div class='clean-report-block'>", unsafe_allow_html=True)
        st.code(compiled_prio_report, language=None)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown(" ")
        col_space, col_clear_w, col_clear_p = st.columns([2, 1, 1])
        with col_clear_w:
            if not eod_df.empty and st.button("🗑️ Clear Logged Work", use_container_width=True):
                archive_df = pd.concat([archive_df, eod_df], ignore_index=True)
                save_and_push(archive_df, ARCHIVE_FILE)
                eod_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS)
                save_and_push(eod_df, EOD_FILE)
                st.rerun()
        with col_clear_p:
            if not prio_df.empty and st.button("🗑️ Clear Staged Priorities", use_container_width=True):
                prio_df = pd.DataFrame(columns=["prio_id", "item_text"])
                save_and_push(prio_df, PRIORITIES_FILE)
                st.rerun()

    # --- TAB 5: TASK HISTORY ---
    with tab_archive:
        st.subheader("📊 Completed Task History")
        
        search_col, filter_col, download_col = st.columns([2.0, 1.5, 1.5], vertical_alignment="bottom")
        with search_col:
            history_search_query = st.text_input("🔍 Search logs by keyword or formula:", value="", placeholder="Type task title, notes, or formulas...", key="hist_search_f")
        with filter_col:
            range_selection = st.selectbox("Choose Date Filter Window:", ["All Logs", "This Week", "This Month", "Custom Date Range"], key="hist_date_f")
            
        if archive_df.empty: 
            st.info("Your master archive file is currently empty.")
        else:
            archive_df['parsed_date'] = archive_df['log_date'].apply(parse_date_safely)
            filter_start, filter_end = today, today
            if range_selection == "This Week":
                filter_start = today - timedelta(days=today.weekday())
                filter_end = filter_start + timedelta(days=6)
            elif range_selection == "This Month":
                filter_start = today.replace(day=1)
                filter_end = (filter_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif range_selection == "Custom Date Range":
                col_date1, col_date2 = st.columns(2)
                with col_date1: filter_start = st.date_input("Start Date Target:", value=today - timedelta(days=7))
                with col_date2: filter_end = st.date_input("End Date Target:", value=today)
            
            filtered_archive = archive_df.copy() if range_selection == "All Logs" else archive_df[(archive_df['parsed_date'] >= filter_start) & (archive_df['parsed_date'] <= filter_end)]
            
            if history_search_query.strip():
                query = history_search_query.lower().strip()
                filtered_archive = filtered_archive[
                    filtered_archive['task_title'].str.lower().str.contains(query) | 
                    filtered_archive['bullet_text'].str.lower().str.contains(query)
                ]
            
            if filtered_archive.empty: 
                st.warning("No archived rows match selected window filters or query term.")
            else:
                st.markdown(f"**Showing Records for Frame: {range_selection}** ({len(filtered_archive)} matches found)")
                filtered_archive = filtered_archive.sort_values(by="parsed_date", ascending=False)
                
                seen_history_blocks = {}
                for _, row in filtered_archive.iterrows():
                    f_date_str = row['parsed_date'].strftime(DATE_FORMAT)
                    title, date_key = row['task_title'], f"📅 Date: {f_date_str}"
                    if date_key not in seen_history_blocks: seen_history_blocks[date_key] = {}
                    if title not in seen_history_blocks[date_key]: seen_history_blocks[date_key][title] = []
                    seen_history_blocks[date_key][title].append((row['bullet_text'], str(row.get('task_links', ''))))
                
                output_lines = []
                for date_lbl, titles_dict in seen_history_blocks.items():
                    output_lines.append(date_lbl); output_lines.append("-" * 40)
                    for title, entries in titles_dict.items():
                        if title == "Manual Log":
                            for note, _ in entries: output_lines.append(f"• {note}")
                        else:
                            output_lines.append(f"• {title}:")
                            for note, extra_links_str in entries:
                                output_lines.append(f"  - {note}")
                                if extra_links_str and extra_links_str != "nan" and extra_links_str.strip():
                                    for lk in extra_links_str.split(","): output_lines.append(f"    🔗 {lk}")
                    output_lines.append("\n")
                
                compiled_text_history = "\n".join(output_lines)
                
                with download_col:
                    st.download_button(
                        label="📥 Download Filtered History (.txt)",
                        data=compiled_text_history,
                        file_name=f"task_history_export_{range_selection.lower().replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                st.markdown("<div class='clean-report-block'>", unsafe_allow_html=True)
                st.code(compiled_text_history, language=None)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("### 💾 Recover Logged File Deliverables")
                file_found = False
                for _, row in filtered_archive.iterrows():
                    raw_b64_data = str(row.get('doc_attachment_b64', '')).strip()
                    if raw_b64_data and raw_b64_data != "nan":
                        file_found = True
                        file_name_label = str(row.get('doc_attachment_name', 'downloaded_file.xlsx'))
                        file_date_stamp = parse_date_safely(row['log_date']).strftime(DATE_FORMAT)
                        
                        try:
                            decoded_binary_payload = base64.b64decode(raw_b64_data)
                            st.download_button(
                                label=f"📥 Download Attached Reference: {file_name_label} ({file_date_stamp})",
                                data=decoded_binary_payload,
                                file_name=file_name_label,
                                mime="application/octet-stream",
                                key=f"dl_btn_{row['log_id']}"
                            )
                        except Exception: pass
                if not file_found:
                    st.caption("No binary files or spreadsheet attachments found inside current archive filter window.")
