import os
import base64
import smtplib
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_calendar import calendar

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
REQUIRED_LOG_COLUMNS = ["log_id", "task_title", "bullet_text", "log_date", "task_links", "screenshot_b64", "doc_attachment_b64", "doc_attachment_name"]

if "editing_task_id" not in st.session_state: st.session_state.editing_task_id = None
if "editing_note_id" not in st.session_state: st.session_state.editing_note_id = None
if "emails_sent_today" not in st.session_state: st.session_state.emails_sent_today = []

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
        payload = {"message": f"🤖 Automated Dashboard Sync: Update {filename}", "content": encoded_content, "branch": branch}
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
    try: df["task_priority"] = pd.to_numeric(df["task_priority"].fillna(3)).astype(int)
    except Exception: df["task_priority"] = 3

if not os.path.exists(EOD_FILE) or os.path.getsize(EOD_FILE) == 0:
    eod_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS)
    eod_df.to_csv(EOD_FILE, index=False)
    push_to_github(EOD_FILE)
else:
    eod_df = pd.read_csv(EOD_FILE)
    eod_df = verify_and_align_columns(eod_df, EOD_FILE, REQUIRED_LOG_COLUMNS)

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
    return 1 if freq_string == "Daily" else 7 if freq_string == "Weekly" else 30

def parse_date_safely(date_str):
    try: return datetime.strptime(str(date_str), STORAGE_DATE_FORMAT).date()
    except ValueError:
        try: return datetime.strptime(str(date_str), DATE_FORMAT).date()
        except ValueError: return datetime.now().date()

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

overdue_tasks_list = []
for _, row in df.iterrows():
    loop_comp_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
    if (today - loop_comp_date).days >= get_days_interval(row.get('frequency', 'Daily')):
        overdue_tasks_list.append(row.get('task_name', 'Unknown Task'))

if overdue_tasks_list:
    alert_summary = f"You have {len(overdue_tasks_list)} items requiring update: " + ", ".join(overdue_tasks_list[:2])
    if len(overdue_tasks_list) > 2: alert_summary += f" and {len(overdue_tasks_list) - 2} more."
    js_code = f"<script>setTimeout(function(){{ if(Notification.permission==='granted'){{ new Notification('⏰ Overdue Routines Alert', {{ body: '{alert_summary}' }}); }} }}, 1000);</script>"
    components.html(js_code, height=0, width=0)

main_layout_frame, right_buffer_column = st.columns([12, 1])
with main_layout_frame:
    st.header("📅 Monthly Overview")
    calendar_events = []
    for _, row in df.iterrows():
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
    for _, row in notes_df.iterrows():
        n_date = parse_date_safely(row['event_date']).strftime(STORAGE_DATE_FORMAT)
        calendar_events.append({"title": f"📌 {row['title']}", "start": n_date, "end": n_date, "backgroundColor": "#334155", "borderColor": "#334155", "allDay": True})
    calendar(events=calendar_events, options={"initialView": "dayGridMonth", "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""}, "editable": False, "selectable": True, "height": "auto", "dayMaxEvents": True, "moreLinkClick": "popover"}, key="monthly_grid_view")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🕒 Performance Analytics & Velocity Insights", expanded=False):
        if not archive_df.empty:
            archive_df['parsed_date'] = archive_df['log_date'].apply(parse_date_safely)
            total_tasks_completed = len(archive_df)
            seven_days_ago = today - timedelta(days=7)
            recent_week_df = archive_df[archive_df['parsed_date'] >= seven_days_ago]
            m_col1, m_col2 = st.columns(2)
            with m_col1: st.metric(label="Total Archived Tasks Closed", value=total_tasks_completed)
            with m_col2: st.metric(label="Tasks Closed (Past 7 Days)", value=len(recent_week_df))
            st.markdown("**Daily Production Velocity Profile:**")
            chart_data = archive_df.groupby('log_date').size().reset_index(name='Tasks Completed').sort_values(by='log_date').tail(10).set_index('log_date')
            st.bar_chart(chart_data, color="#38BDF8")
        else:
            st.info("Analytics metrics will populate automatically here as actions are moved into the history archives.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.header("🖥️ Command Center 🖥️")
    tab_alerts, tab_add, tab_manage, tab_eod, tab_archive = st.tabs(["⚠️ Pending Tasks", "➕ New Task", "⚡ Existing Task", "📑 EOD Report", "🕒 Task History"])

    with tab_alerts:
        st.subheader("Pending Tasks")
        active_pending_df = df.copy()
        if "task_priority" in active_pending_df.columns:
            active_pending_df["task_priority"] = pd.to_numeric(active_pending_df["task_priority"]).fillna(3).astype(int)
            active_pending_df = active_pending_df.sort_values(by="task_priority", ascending=False)
        reminders_found = False
        for _, row in active_pending_df.iterrows():
            last_comp_date = parse_date_safely(row.get('last_completed', today.strftime(STORAGE_DATE_FORMAT)))
            if (today - last_comp_date).days >= get_days_interval(row.get('frequency', 'Daily')):
                reminders_found = True
                star_render_string = "⭐" * int(row.get('task_priority', 3))
                type_label = "📌 One-Time" if str(row.get('is_recurring', 'Yes')) == "No" else "🔄 Recurring"
                st.markdown(f"### **{row.get('task_name', 'Unnamed Task')}** <span class='stars-container'>{star_render_string}</span>", unsafe_allow_html=True)
                st.caption(f"Cycle: {row.get('frequency', 'Daily')} — *{type_label}*")
                desc_content = str(row.get('task_description', 'No instructions.'))
                lines = desc_content.split("\n")
                if any(line.strip().startswith("=") for line in lines):
                    yes_f, no_f, plain = [], [], []
                    curr_b = None
                    for line in lines:
                        cl = line.strip()
                        if not cl: continue
                        if cl.lower() == "yes": curr_b = "yes"
                        elif cl.lower() == "no": curr_b = "no"
                        elif cl.startswith("="):
                            if curr_b == "yes": yes_f.append(cl)
                            elif curr_b == "no": no_f.append(cl)
                            else: plain.append(cl)
                        elif cl.lower() not in ["formula to use:", "formula to use"]: plain.append(cl)
                    for inst in plain: st.markdown(f"**{inst}**")
                    st.markdown("#### **📋 Formula to Use:**")
                    gc1, gc2 = st.columns(2, gap="medium")
                    with gc1:
                        st.markdown("<span style='color:#38BDF8; font-weight:bold;'>🟢 In Stock:</span>", unsafe_allow_html=True)
                        for f_item in yes_f: st.markdown(f"<div class='clean-copy'>{st.code(f_item, language=None)}</div>", unsafe_allow_html=True)
                    with gc2:
                        st.markdown("<span style='color:#94A3B8; font-weight:bold;'>🔴 Out of Stock:</span>", unsafe_allow_html=True)
                        for f_item in no_f: st.markdown(f"<div class='clean-copy'>{st.code(f_item, language=None)}</div>", unsafe_allow_html=True)
                else: st.write(desc_content)
                links = str(row.get('task_url', '')).strip()
                if links and links != "nan":
                    l_cols = st.columns(min(max(len(links.split(",")), 1), 4))
                    for idx, url in enumerate(links.split(",")):
                        if url.strip():
                            with l_cols[idx % 4]: st.link_button(f"🔗 Open Reference Link", url=url.strip(), use_container_width=True)
                img_b64 = str(row.get('task_screenshot_b64', '')).strip()
                if img_b64 and img_b64 != "nan":
                    try: st.image(base64.b64decode(img_b64), caption="Reference Screenshot", width=350)
                    except Exception: pass
                st.markdown("<div class='pending-row-form'>", unsafe_allow_html=True)
                with st.form(key=f"form_pending_{row.get('task_id')}"):
                    res_n = st.text_area("Action Notes / Results Summary:", placeholder="Type verification updates here...", height=68)
                    up_doc = st.file_uploader("📎 Attach Deliverable Document:", type=["xlsx", "xls", "docx", "doc", "pdf", "csv"])
                    if st.form_submit_button("Done"):
                        doc_b64, doc_name = "", ""
                        if up_doc is not None:
                            doc_b64 = base64.b64encode(up_doc.read()).decode('utf-8')
                            doc_name = up_doc.name
                        new_log = {
                            "log_id": int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1,
                            "task_title": str(row.get('task_name', 'Manual Log')).strip(),
                            "bullet_text": res_n.strip() if res_n.strip() else "Completed successfully.",
                            "log_date": today.strftime(STORAGE_DATE_FORMAT),
                            "task_links": str(row.get('task_url', '')),
                            "screenshot_b64": str(row.get('task_screenshot_b64', '')),
                            "doc_attachment_b64": doc_b64,
                            "doc_attachment_name": doc_name
                        }
                        eod_df = pd.concat([eod_df, pd.DataFrame([new_log])], ignore_index=True)
                        save_and_push(eod_df, EOD_FILE)
                        idx = df[df['task_id'] == row.get('task_id')].index
                        if not idx.empty:
                            if str(row.get('is_recurring', 'Yes')) == "No": df = df.drop(idx)
                            else: df.at[idx[0], 'last_completed'] = today.strftime(STORAGE_DATE_FORMAT)
                            save_and_push(df, DB_FILE)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:1.5em 0px; border-color:#232936;'>", unsafe_allow_html=True)
        if not reminders_found: st.success("🎉 Everything is running on schedule!")

    with tab_add:
        st_t, st_n = st.tabs(["🔄 Recurring Routine", "📌 One-Time Note"])
        with st_t:
            with st.form("new_task_form", clear_on_submit=True):
                n_name = st.text_input("Task Title")
                n_desc = st.text_area("Instructions & Specific Formulas")
                b_urls = st.text_area("Task Resource URLs (Paste one per line):")
                up_media = st.file_uploader("Attach Base Reference Screenshot:", type=["png", "jpg", "jpeg"])
                c1, c2, c3 = st.columns(3)
                with c1: n_freq = st.selectbox("Interval Cycle", ["Daily", "Weekly", "Monthly"])
                with c2: n_rec = st.selectbox("Is this task recurring?", ["Yes", "No"])
                with c3: n_star = st.selectbox("Assign Priority Star Level:", STAR_OPTIONS, index=2)
                if st.form_submit_button("Save Routine") and n_name:
                    n_id = int(df['task_id'].max() + 1) if not df.empty else 1
                    n_row = {
                        "task_id": n_id, "task_name": n_name, "task_description": n_desc if n_desc else "No instructions.",
                        "task_url": ",".join([l.strip() for l in b_urls.split("\n") if l.strip()]),
                        "frequency": n_freq, "is_recurring": n_rec, "last_completed": today.strftime(STORAGE_DATE_FORMAT),
                        "task_screenshot_b64": base64.b64encode(up_media.read()).decode('utf-8') if up_media else "",
                        "task_priority": STAR_OPTIONS.index(n_star) + 1
                    }
                    df = pd.concat([df, pd.DataFrame([n_row])], ignore_index=True)
                    save_and_push(df, DB_FILE)
                    st.rerun()
        with st_n:
            with st.form("new_note_form", clear_on_submit=True):
                nt = st.text_input("Meeting / Event Title")
                nd = st.text_area("Agenda Notes")
                if st.form_submit_button("Pin to Calendar") and nt:
                    nid = int(notes_df['note_id'].max() + 1) if not notes_df.empty else 1
                    notes_df = pd.concat([notes_df, pd.DataFrame([{"note_id": nid, "title": nt, "details": nd, "event_date": today.strftime(STORAGE_DATE_FORMAT)}])], ignore_index=True)
                    save_and_push(notes_df, NOTES_FILE)
                    st.rerun()

    with tab_manage:
        st.subheader("Edit & Delete Settings")
        m_t, m_n, m_d = st.tabs(["Rotations", "Calendar Notes", "⚠️ Factory Reset"])
        with m_t:
            m_df = df.copy()
            if "task_priority" in m_df.columns:
                m_df["task_priority"] = pd.to_numeric(m_df["task_priority"]).fillna(3).astype(int)
                m_df = m_df.sort_values(by="task_priority", ascending=False)
            for _, row in m_df.iterrows():
                ec1, ec2, ec3 = st.columns([2.5, 1.5, 1.0])
                tid = row.get('task_id')
                if st.session_state.editing_task_id == tid:
                    with ec1:
                        en = st.text_input("Name", value=row.get('task_name', ''), key=f"en_{tid}", label_visibility="collapsed")
                        ed = st.text_area("Desc", value=row.get('task_description', ''), key=f"ed_{tid}", label_visibility="collapsed")
                        eu = st.text_input("URL", value=str(row.get('task_url', '')), key=f"eurl_{tid}")
                    with ec2:
                        ef = st.selectbox("Freq", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(row.get('frequency', 'Daily')), key=f"ef_{tid}", label_visibility="collapsed")
                        er = st.selectbox("Rec", ["Yes", "No"], index=["Yes", "No"].index(str(row.get('is_recurring', 'Yes')) if str(row.get('is_recurring', 'Yes')) in ["Yes", "No"] else "Yes"), key=f"erec_{tid}", label_visibility="collapsed")
                        es = st.selectbox("Prio", STAR_OPTIONS, index=int(row.get('task_priority', 3))-1, key=f"eprio_{tid}")
                    with ec3:
                        if st.button("✅", key=f"s_{tid}"):
                            idx = df[df['task_id'] == tid].index[0]
                            df.at[idx, ['task_name', 'task_description', 'task_url', 'frequency', 'is_recurring', 'task_priority']] = [en, ed, eu.strip(), ef, er, STAR_OPTIONS.index(es) + 1]
                            save_and_push(df, DB_FILE); st.session_state.editing_task_id = None; st.rerun()
                else:
                    with ec1: st.write(f"**{row.get('task_name', 'Task')}** — <span class='stars-container'>{'⭐'*int(row.get('task_priority', 3))}</span>", unsafe_allow_html=True)
                    with ec2:
                        if st.button("✒️", key=f"em_{tid}"): st.session_state.editing_task_id = tid; st.rerun()
                    with ec3:
                        if st.button("♻️", key=f"d_{tid}"):
                            df = df.drop(df[df['task_id'] == tid].index[0])
                            save_and_push(df, DB_FILE); st.rerun()
                st.markdown("<hr style='margin:0.05em 0px; border-color:#232936;'>", unsafe_allow_html=True)
        with m_n:
            if notes_df.empty: st.info("No notes.")
            else:
                for _, row in notes_df.iterrows():
                    nc1, nc2, nc3 = st.columns([3, 1, 1])
                    if st.session_state.editing_note_id == row['note_id']:
                        with nc1:
                            ent = st.text_input("T", value=row['title'], key=f"ent_{row['note_id']}", label_visibility="collapsed")
                            end = st.text_area("D", value=row['details'], key=f"end_{row['note_id']}", label_visibility="collapsed")
                        with nc3:
                            if st.button("✅", key=f"s_note_{row['note_id']}"):
                                idx = notes_df[notes_df['note_id'] == row['note_id']].index[0]
                                notes_df.at[idx, ['title', 'details']] = [ent, end]
                                save_and_push(notes_df, NOTES_FILE); st.session_state.editing_note_id = None; st.rerun()
                    else:
                        with nc1: st.write(f"📌 **{row['title']}**")
                        with nc2:
                            if st.button("✒️", key=f"em_note_{row['note_id']}"): st.session_state.editing_note_id = row['note_id']; st.rerun()
                        with nc3:
                            if st.button("♻️", key=f"del_note_{row['note_id']}"):
                                notes_df = notes_df[notes_df['note_id'] != row['note_id']]
                                save_and_push(notes_df, NOTES_FILE); st.rerun()
                    st.markdown("<hr style='margin:0.05em 0px; border-color:#232936;'>", unsafe_allow_html=True)
        with m_d:
            if st.text_input("Type RESET ALL:") == "RESET ALL" and st.button("💥 WIPE"):
                df = pd.DataFrame(get_starter_tasks()); save_and_push(df, DB_FILE)
                for f in [NOTES_FILE, EOD_FILE, PRIORITIES_FILE, ARCHIVE_FILE]:
                    if os.path.exists(f): os.remove(f)
                st.session_state.editing_task_id = st.session_state.editing_note_id = None; st.rerun()

    with tab_eod:
        st.subheader("Daily Task Report")
        with st.columns(2)[0].form("eod_add_form", clear_on_submit=True):
            mt = st.text_input("Title", value="Manual Log")
            li = st.text_input("Detail")
            if st.form_submit_button("Add") and li:
                new_row = {"log_id": int(eod_df['log_id'].max() + 1) if not eod_df.empty else 1, "task_title": mt.strip() or "Manual Log", "bullet_text": li.strip(), "log_date": today.strftime(STORAGE_DATE_FORMAT), "task_links": "", "screenshot_b64": "", "doc_attachment_b64": "", "doc_attachment_name": ""}
                eod_df = pd.concat([eod_df, pd.DataFrame([new_row])], ignore_index=True); save_and_push(eod_df, EOD_FILE); st.rerun()
        st.markdown("**EOD Summary Block:**")
        st.markdown(f"<div class='clean-report-block'>{st.code(f'Date: {today.strftime(DATE_FORMAT)}\nCompleted Tasks:\n' + '\n'.join([f'• {row.task_title}: {row.bullet_text}' for _, row in eod_df.iterrows()]), language=None)}</div>", unsafe_allow_html=True)
        with st.columns([2, 1, 1])[1]:
            if not eod_df.empty and st.button("✅ Clear Task Log"):
                archive_df = pd.concat([archive_df, eod_df], ignore_index=True); save_and_push(archive_df, ARCHIVE_FILE); eod_df = pd.DataFrame(columns=REQUIRED_LOG_COLUMNS); save_and_push(eod_df, EOD_FILE); st.rerun()

    with tab_archive:
        st.subheader("🕒 Completed Task History")
        h_q = st.text_input("🔍 Search:")
        if archive_df.empty: st.info("Empty.")
        else:
            arch_filtered = archive_df
            if h_q.strip(): arch_filtered = arch_filtered[arch_filtered['task_title'].str.contains(h_q, case=False)]
            st.code('\n'.join([f"{row.log_date} | {row.task_title}: {row.bullet_text}" for _, row in arch_filtered.iterrows()]), language=None)
