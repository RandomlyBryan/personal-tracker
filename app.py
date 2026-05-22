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
ARCHIVE_FILE = "eod_master_archive.csv"
DATE_FORMAT = "%d/%m/%Y"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

# Initialize temporary memory states
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "editing_note_id" not in st.session_state:
    st.session_state.editing_note_id = None
if "emails_sent_today" not in st.session_state:
    st.session_state.emails_sent_today = []

def get_starter_tasks():
    return {
        "task_id": [1, 2, 3],
        "task_name": ["Daily Standup Check", "Weekly App Sync", "Monthly Budget Check"],
        "task_description": ["Review code checklist.", "Verify remote logs.", "Export statements."],
        "task_url": ["", "", ""],
        "frequency": ["Daily", "Weekly", "Monthly"],
        "is_recurring": ["Yes", "Yes", "Yes"],
        "last_completed": [
            (datetime.now() - timedelta(days=2)).strftime(STORAGE_DATE_FORMAT), 
            (datetime.now() - timedelta(days=8)).strftime(STORAGE_DATE_FORMAT), 
            (datetime.now() - timedelta(days=32)).strftime(STORAGE_DATE_FORMAT)
        ]
    }

# Load/Initialize Databases
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(get_starter_tasks())
    df.to_csv(DB_FILE, index=False)
else:
    df = pd.read_csv(DB_FILE)
    if "task_url" not in df.columns:
        df["task_url"] = ""
    if "is_recurring" not in df.columns:
        df["is_recurring"] = "Yes"
    df.to_csv(DB_FILE, index=False)
    df["task_url"] = df["task_url"].fillna("").astype(str)
    df["is_recurring"] = df["is_recurring"].fillna("Yes").astype(str)

if not os.path.exists(EOD_FILE):
    eod_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date"])
    eod_df.to_csv(EOD_FILE, index=False)
else:
    eod_df = pd.read_csv(EOD_FILE)
    if "task_title" not in eod_df.columns:
        eod_df["task_title"] = "Manual Log"
    if "log_date" not in eod_df.columns:
        eod_df["log_date"] = datetime.now().strftime(STORAGE_DATE_FORMAT)
    eod_df.to_csv(EOD_FILE, index=False)
    eod_df["task_title"] = eod_df["task_title"].fillna("Manual Log").astype(str)
    eod_df["bullet_text"] = eod_df["bullet_text"].fillna("").astype(str)

if not os.path.exists(ARCHIVE_FILE):
    archive_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date"])
    archive_df.to_csv(ARCHIVE_FILE, index=False)
else:
    archive_df = pd.read_csv(ARCHIVE_FILE)
    archive_df["log_date"] = archive_df["log_date"].fillna(datetime.now().strftime(STORAGE_DATE_FORMAT)).astype(str)

if not os.path.exists(NOTES_FILE):
    notes_df = pd.DataFrame(columns=["note_id", "title", "details", "event_date"])
    notes_df.to_csv(NOTES_FILE, index=False)
else:
    notes_df = pd.read_csv(NOTES_FILE)

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

if overdue_tasks_list:
    alert_summary = f"You have {len(overdue_tasks_list)} items requiring update: " + ", ".join(overdue_tasks_list[:2])
    if len(overdue_tasks_list) > 2:
        alert_summary += f" and {len(overdue_tasks_list) - 2} more."

    js_notification_code = f"""
    <script>
    function triggerDesktopPush() {{
        if (!("Notification" in window)) return;
        if (Notification.permission === "granted") {{
            new Notification("⏰ Overdue Routines Alert", {{ body: "{alert_summary}", icon: "https://cdn-icons-png.flaticon.com/512/599/599502.png" }});
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission().then(function (permission) {{
                if (permission === "granted") {{
                    new Notification("⏰ Overdue Routines Alert", {{ body: "{alert_summary}", icon: "https://cdn-icons-png.flaticon.com/512/599/599502.png" }});
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
    
    tab_alerts, tab_eod, tab_archive, tab_add, tab_manage = st.tabs([
        "🚨 Pending Tasks", 
        "📝 EOD Report", 
        "📊 Archive Viewer", 
        "➕ New Task", 
        "⚙️ Existing Task"
    ])
    
    # --- TAB 1: PENDING TASKS & ALERTS ---
    with tab_alerts:
        st.subheader("Items Due For Update")
        reminders_found = False
        
        for index, row in df.copy().iterrows():
            last_comp_date = parse_date_safely(row['last_completed'])
            days_since = (today - last_comp_date).days
            needed_days = get_days_interval(row['frequency'])
            
            if days_since >= needed_days:
                reminders_found = True
                col_text, col_action = st.columns([1.8, 1.2])
                with col_text:
                    type_label = "📌 One-Time" if str(row.get('is_recurring', 'Yes')) == "No" else "🔄 Recurring"
                    st.warning(f"**{row['task_name']}** ({row['frequency']} — *{type_label}*)")
                    with st.expander("📄 View Instructions & Links"):
                        st.write(row['task_description'])
                        task_link = str(row.get('task_url', '')).strip()
                        if task_link and task_link != "nan" and task_link != "":
                            st.link_button("🔗 Open Direct Link", url=task_link, use_container_width=True)
                    
                    if row['task_id'] not in st.session_state.emails_sent_today:
                        t_desc = row['task_description'] if pd.notna(row['task_description']) else "No instructions provided."
                        t_url = row['task_url'] if pd.notna(row['task_url']) else ""
                        if send_email_notification(row['task_name'], days_since, t_desc, t_url):
                            st.session_state.emails_sent_today.append(row['task_id'])
                            st.info(f"📧 Notification dispatched!")
                
                with col_action:
                    result_notes = st.text_input("Action Notes / Results:", placeholder="e.g., 8 books found, etc.", key=f"res_{row['task_id']}")
                    if st.button("Done", key=f"remind_btn_{row['task_id']}", use_container_width=True):
                        clean_notes = result_notes.strip() if result_notes.strip() else "Completed successfully."
                        
                        new_log_id = int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1
                        new_log_row = {
                            "log_id": new_log_id, 
                            "task_title": str(row['task_name']).strip(), 
                            "bullet_text": clean_notes,
                            "log_date": today.strftime(STORAGE_DATE_FORMAT)
                        }
                        eod_df = pd.concat([eod_df, pd.DataFrame([new_log_row])], ignore_index=True)
                        save_db(eod_df, EOD_FILE)
                        
                        if str(row.get('is_recurring', 'Yes')) == "No":
                            df = df[df['task_id'] != row['task_id']]
                        else:
                            df.at[index, 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                        
                        save_db(df, DB_FILE)
                        if row['task_id'] in st.session_state.emails_sent_today:
                            st.session_state.emails_sent_today.remove(row['task_id'])
                        st.rerun()
                st.markdown("<hr style='margin:0.4em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)
                        
        if not reminders_found:
            st.success("🎉 Everything is running on schedule!")
            
    # --- TAB 2: EOD REPORT LOG BUILDER ---
    with tab_eod:
        st.subheader("Daily Task Report")
        st.markdown("**📋 Quick Copy**")
        st.code("Bryan Reyes\nwork.bryanc@gmail.com\nMarketing & Reporting VA", language=None)
        st.markdown("---")
        
        eod_log_col, prio_log_col = st.columns(2)
        with eod_log_col:
            st.markdown("**Add Completed Tasks:**")
            with st.form("eod_add_form", clear_on_submit=True):
                manual_title = st.text_input("Project / Task Title:", value="Manual Log")
                log_input = st.text_input("Action Detail / Note:")
                add_bullet = st.form_submit_button("Add")
                if add_bullet and log_input:
                    new_log_id = int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1
                    new_log_row = {
                        "log_id": new_log_id, 
                        "task_title": manual_title.strip() if manual_title.strip() else "Manual Log", 
                        "bullet_text": log_input.strip(),
                        "log_date": today.strftime(STORAGE_DATE_FORMAT)
                    }
                    eod_df = pd.concat([eod_df, pd.DataFrame([new_log_row])], ignore_index=True)
                    save_db(eod_df, EOD_FILE)
                    st.rerun()
                    
        with prio_log_col:
            st.markdown("**Next Day Task Priorities:**")
            with st.form("prio_add_form", clear_on_submit=True):
                prio_input = st.text_input("Item for tomorrow:", key="prio_in")
                add_prio = st.form_submit_button("Add")
                if add_prio and prio_input:
                    new_prio_id = int(prio_df['prio_id'].max() + 1) if not prio_df.empty else 1
                    new_prio_row = {"prio_id": new_prio_id, "item_text": prio_input.strip()}
                    prio_df = pd.concat([prio_df, pd.DataFrame([new_prio_row])], ignore_index=True)
                    save_db(prio_df, PRIORITIES_FILE)
                    st.rerun()

        st.markdown("---")

        emp_header = (
            f"Date: {today.strftime(DATE_FORMAT)}\n"
            f"----------------------------------------\n"
            f"Completed Tasks & Actions Log:\n"
        )
        
        if not eod_df.empty:
            grouped_lines = []
            seen_titles = {}
            for _, row in eod_df.iterrows():
                title = row['task_title']
                note = row['bullet_text']
                if title not in seen_titles:
                    seen_titles[title] = []
                seen_titles[title].append(note)
            
            for title, notes in seen_titles.items():
                if title == "Manual Log":
                    for note in notes: grouped_lines.append(f"• {note}")
                else:
                    grouped_lines.append(f"• {title}:")
                    for note in notes: grouped_lines.append(f"  - {note}")
                        
            compiled_report = f"{emp_header}" + "\n".join(grouped_lines)
        else:
            compiled_report = f"{emp_header}• (No work logged yet today.)"
            
        st.markdown("**EOD Summary:**")
        st.code(compiled_report, language=None)
        
        auto_priorities = []
        for _, row in df.iterrows():
            l_completed = parse_date_safely(row['last_completed'])
            d_since = (today - l_completed).days
            i_window = get_days_interval(row['frequency'])
            n_due = l_completed + timedelta(days=i_window)
            
            if d_since >= i_window:
                auto_priorities.append(f"• [ROLLOVER] {row['task_name']} (Overdue)")
            elif n_due == tomorrow:
                auto_priorities.append(f"• [SCHEDULED] {row['task_name']} (Due Tomorrow)")
                
        for _, row in prio_df.iterrows(): auto_priorities.append(f"• {row['item_text']}")
            
        prio_header = f"Next Day Priorities / Agenda ({tomorrow.strftime(DATE_FORMAT)}):\n----------------------------------------\n"
        compiled_prio_report = prio_header + ("\n".join(auto_priorities) if auto_priorities else "• No priorities scheduled for tomorrow.")
            
        st.markdown("**Next Day Priorities:**")
        st.code(compiled_prio_report, language=None)
        
        st.markdown(" ")
        col_space, col_clear_w, col_clear_p = st.columns([2, 1, 1])
        with col_clear_w:
            if not eod_df.empty and st.button("🗑️ Clear Logged Work", use_container_width=True):
                archive_df = pd.concat([archive_df, eod_df], ignore_index=True)
                save_db(archive_df, ARCHIVE_FILE)
                eod_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date"])
                save_db(eod_df, EOD_FILE)
                st.rerun()
        with col_clear_p:
            if not prio_df.empty and st.button("🗑️ Clear Staged Priorities", use_container_width=True):
                prio_df = pd.DataFrame(columns=["prio_id", "item_text"])
                save_db(prio_df, PRIORITIES_FILE)
                st.rerun()

    # --- TAB 3: MASTER ARCHIVE HISTORIC VIEW (WITH FIXED HORIZONTAL ALIGNMENT) ---
    with tab_archive:
        st.subheader("📊 Completed Work History Archive")
        
        # FIXED LAYOUT GRID: Added vertical_alignment="bottom" to align the dropdown and expander perfectly
        col_drop, col_reset = st.columns([1.8, 1.2], gap="large", vertical_alignment="bottom")
        
        with col_drop:
            range_selection = st.selectbox("Choose Date Filter Window:", ["All Logs", "This Week", "This Month", "Custom Date Range"])
        
        with col_reset:
            with st.expander("🗑️ Clear History Logs"):
                st.caption("Permanently clear your master historic archive file (`eod_master_archive.csv`). This won't affect active or pending tasks.")
                confirm_history_wipe = st.checkbox("Confirm permanent delete of all history rows", key="hist_wipe_check")
                if confirm_history_wipe:
                    if st.button("💥 Wipe History File", use_container_width=True):
                        archive_df = pd.DataFrame(columns=["log_id", "task_title", "bullet_text", "log_date"])
                        save_db(archive_df, ARCHIVE_FILE)
                        st.success("History database cleared!")
                        st.rerun()

        filter_start = today
        filter_end = today
        
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
                
        if archive_df.empty:
            st.info("Your master archive file is currently empty.")
        else:
            archive_df['parsed_date'] = archive_df['log_date'].apply(parse_date_safely)
            filtered_archive = archive_df.copy() if range_selection == "All Logs" else archive_df[(archive_df['parsed_date'] >= filter_start) & (archive_df['parsed_date'] <= filter_end)]
                
            if filtered_archive.empty:
                st.warning(f"No archived rows match selected window filter.")
            else:
                st.markdown(f"**Showing Records for Frame: {range_selection}** ({len(filtered_archive)} actions logged)")
                filtered_archive = filtered_archive.sort_values(by="parsed_date", ascending=False)
                
                seen_history_blocks = {}
                for _, row in filtered_archive.iterrows():
                    f_date_str = row['parsed_date'].strftime(DATE_FORMAT)
                    title = row['task_title']
                    note = row['bullet_text']
                    date_key = f"📅 Date: {f_date_str}"
                    if date_key not in seen_history_blocks: seen_history_blocks[date_key] = {}
                    if title not in seen_history_blocks[date_key]: seen_history_blocks[date_key][title] = []
                    seen_history_blocks[date_key][title].append(note)
                
                output_lines = []
                for date_lbl, titles_dict in seen_history_blocks.items():
                    output_lines.append(date_lbl)
                    output_lines.append("-" * 40)
                    for title, notes in titles_dict.items():
                        if title == "Manual Log":
                            for note in notes: output_lines.append(f"• {note}")
                        else:
                            output_lines.append(f"• {title}:")
                            for note in notes: output_lines.append(f"  - {note}")
                    output_lines.append("\n")
                st.code("\n".join(output_lines), language=None)

    # --- TAB 4: DATA CREATION FORMS ---
    with tab_add:
        sub_tab_task, sub_tab_note = st.tabs(["🔄 Recurring Routine", "📌 One-Time Note"])
        with sub_tab_task:
            with st.form("new_task_form", clear_on_submit=True):
                new_name = st.text_input("Task Title")
                new_desc = st.text_area("Instructions")
                new_url = st.text_input("Task URL Link (Optional)")
                col_f1, col_f2 = st.columns(2)
                with col_f1: new_freq = st.selectbox("Interval Cycle", ["Daily", "Weekly", "Monthly"])
                with col_f2: recurrence_setting = st.selectbox("Is this task recurring?", ["Yes", "No"])
                start_date = st.date_input("Routine Start Date", value=today)
                submitted = st.form_submit_button("Save Routine")
                if submitted and new_name:
                    new_id = int(df['task_id'].max() + 1) if not df.empty else 1
                    new_row = {"task_id": new_id, "task_name": new_name, "task_description": new_desc if new_desc else "No instructions.", "task_url": new_url.strip(), "frequency": new_freq, "is_recurring": recurrence_setting, "last_completed": start_date.strftime(STORAGE_DATE_FORMAT)}
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
                    new_note_row = {"note_id": new_note_id, "title": note_title, "details": note_details if note_details else "", "event_date": note_date.strftime(STORAGE_DATE_FORMAT)}
                    notes_df = pd.concat([notes_df, pd.DataFrame([new_note_row])], ignore_index=True)
                    save_db(notes_df, NOTES_FILE)
                    st.rerun()

    # --- TAB 5: MAINTENANCE LISTS & FACTORY RESET ---
    with tab_manage:
        st.subheader("Edit & Delete Settings")
        m_task, m_note, m_danger = st.tabs(["Rotations", "Calendar Notes", "⚠️ Factory Reset"])
        
        with m_task:
            for index, row in df.iterrows():
                ec1, ec2, ec3 = st.columns([3, 1, 1])
                current_task_date = parse_date_safely(row['last_completed'])
                if st.session_state.editing_task_id == row['task_id']:
                    with ec1:
                        edit_name = st.text_input("Name", value=row['task_name'], key=f"en_{row['task_id']}", label_visibility="collapsed")
                        edit_desc = st.text_area("Desc", value=row['task_description'], key=f"ed_{row['task_id']}", label_visibility="collapsed")
                        current_url_raw = row.get('task_url', '')
                        edit_url = st.text_input("URL Link", value=str(current_url_raw) if pd.notna(current_url_raw) else "", key=f"eurl_{row['task_id']}")
                    with ec2:
                        edit_freq = st.selectbox("Freq", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row['frequency']), key=f"ef_{row['task_id']}", label_visibility="collapsed")
                        current_rec_val = str(row.get('is_recurring', 'Yes'))
                        edit_rec = st.selectbox("Recurring?", ["Yes", "No"], index=["Yes", "No"].index(current_rec_val if current_rec_val in ["Yes", "No"] else "Yes"), key=f"erec_{row['task_id']}")
                        edit_t_date = st.date_input("Edit Start Date", value=current_task_date, key=f"etd_{row['task_id']}", label_visibility="collapsed")
                    with ec3:
                        if st.button("💾", key=f"s_{row['task_id']}"):
                            df.at[index, 'task_name'] = edit_name
                            df.at[index, 'task_description'] = edit_desc
                            df.at[index, 'task_url'] = edit_url.strip()
                            df.at[index, 'frequency'] = edit_freq
                            df.at[index, 'is_recurring'] = edit_rec
                            df.at[index, 'last_completed'] = edit_t_date.strftime(STORAGE_DATE_FORMAT)
                            save_db(df, DB_FILE)
                            st.session_state.editing_task_id = None
                            st.rerun()
                else:
                    with ec1:
                        rec_txt = "One-Time" if str(row.get('is_recurring', 'Yes')) == "No" else "Recurring"
                        st.write(f"**{row['task_name']}** ({row['frequency']} — *{rec_txt}*)")
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
                st.markdown("<hr style='margin:0.05em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)

        with m_note:
            if notes_df.empty: st.info("No temporary calendar notes pinned.")
            else:
                for index, row in notes_df.iterrows():
                    nc1, nc2, nc3 = st.columns([3, 1, 1])
                    if st.session_state.editing_note_id == row['note_id']:
                        current_note_date = parse_date_safely(row['event_date'])
                        with nc1:
                            edit_note_title = st.text_input("Edit Note Title", value=row['title'], key=f"ent_{row['note_id']}", label_visibility="collapsed")
                            edit_note_details = st.text_area("Edit Note Details", value=row['details'], key=f"end_{row['note_id']}", label_visibility="collapsed")
                        with nc2: edit_note_date = st.date_input("Edit Note Date", value=current_note_date, key=f"endate_{row['note_id']}", label_visibility="collapsed")
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
                                with st.expander("📄 View Agenda Notes"): st.write(row['details'])
                        with nc2:
                            if st.button("✏️", key=f"em_note_{row['note_id']}"):
                                st.session_state.editing_note_id = row['note_id']
                                st.rerun()
                        with nc3:
                            if st.button("🗑️", key=f"del_note_{row['note_id']}"):
                                notes_df = notes_df[notes_df['note_id'] != row['note_id']]
                                save_db(notes_df, NOTES_FILE)
                                st.rerun()
                    st.markdown("<hr style='margin:0.05em 0px; border-color:#f0f2f6;'>", unsafe_allow_html=True)
                    
        with m_danger:
            st.warning("🚨 **CRITICAL ZONE: Full Factory Reset Dashboard**")
            st.write("This tool will permanently delete all your task data, calendar notes, ongoing EOD stagers, and deep history archives, recreating pristine default starter files.")
            confirm_input = st.text_input("Type **RESET ALL** to unlock confirmation:", placeholder="RESET ALL")
            if confirm_input == "RESET ALL":
                if st.button("💥 WIPE ALL TRACKER REPOSITORIES", use_container_width=True):
                    df = pd.DataFrame(get_starter_tasks())
                    save_db(df, DB_FILE)
                    for target_csv in [NOTES_FILE, EOD_FILE, PRIORITIES_FILE, ARCHIVE_FILE]:
                        if os.path.exists(target_csv): os.remove(target_csv)
                    st.success("System reset successful! Rebooting tracker dashboard...")
                    st.session_state.editing_task_id = None
                    st.session_state.editing_note_id = None
                    st.session_state.emails_sent_today = []
                    st.rerun()

# ------------------------------------------
# RIGHT PANEL: FLUID VISUAL CALENDAR
# ------------------------------------------
with right_panel:
    st.header("📅 Monthly Overview")
    calendar_events = []
    
    for index, row in df.iterrows():
        base_date = parse_date_safely(row['last_completed'])
        target_span = get_days_interval(row['frequency'])
        next_due = base_date + timedelta(days=target_span)
        is_overdue = today >= next_due
        event_color = "#FF4B4B" if is_overdue else "#1C83E1"
        prio_marker = "📌" if str(row.get('is_recurring', 'Yes')) == "No" else "🔄"
        calendar_events.append({
            "title": f"⚠️ Due: {row['task_name']}" if is_overdue else f"{prio_marker} {row['task_name']}",
            "start": next_due.strftime(STORAGE_DATE_FORMAT), "end": next_due.strftime(STORAGE_DATE_FORMAT),
            "backgroundColor": event_color, "borderColor": event_color, "allDay": True
        })
        
    for index, row in notes_df.iterrows():
        n_date = parse_date_safely(row['event_date']).strftime(STORAGE_DATE_FORMAT)
        calendar_events.append({
            "title": f"📌 {row['title']}", "start": n_date, "end": n_date,
            "backgroundColor": "#7A41F3", "borderColor": "#7A41F3", "allDay": True
        })
        
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": { "left": "prev,next today", "center": "title", "right": "" },
        "editable": False, "selectable": True, "height": "auto",
        "dayMaxEvents": True, "moreLinkClick": "popover"
    }
    calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
