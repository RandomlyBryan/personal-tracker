import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. Page Configuration
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database File Setup
DB_FILE = "tasks_db.csv"
DATE_FORMAT = "%d/%m/%Y"

# Initialize our temporary memory (session state) for handling edits
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None

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
        with col_btn:
            if st.button("Mark Completed", key=f"remind_btn_{row['task_id']}"):
                df.at[index, 'last_completed'] = today.strftime(DATE_FORMAT)
                save_db(df)
                st.rerun()

if not reminders_found:
    st.success("All clear! Your recurring tasks are up to date.")

st.markdown("---")

# --- PART 3: MASTER SCHEDULE INTERFACE (WITH EDIT/DELETE) ---
st.subheader("📋 Master Schedule Overview")

# Table Headers
hdr_col1, hdr_col2, hdr_col3, hdr_col4, hdr_col5 = st.columns([3, 1, 1, 1, 1])
hdr_col1.markdown("**Task Name**")
hdr_col2.markdown("**Frequency**")
hdr_col3.markdown("**Last Completed**")
hdr_col4.markdown("**Next Due Date**")
hdr_col5.markdown("**Actions**")

# Loop through and build custom rows with action buttons
for index, row in df.iterrows():
    base_date = datetime.strptime(str(row['last_completed']), DATE_FORMAT).date()
    next_due = base_date + timedelta(days=7) if row['frequency'] == "Weekly" else base_date + timedelta(days=30)
    
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    # CHECK: Is this specific row currently being edited?
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
                if st.button("💾", key=f"save_{row['task_id']}", help="Save changes"):
                    df.at[index, 'task_name'] = edit_name
                    df.at[index, 'frequency'] = edit_freq
                    save_db(df)
                    st.session_state.editing_task_id = None
                    st.rerun()
            with btn_cancel:
                if st.button("❌", key=f"cancel_{row['task_id']}", help="Cancel editing"):
                    st.session_state.editing_task_id = None
                    st.rerun()
    else:
        # Standard View Mode
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
                if st.button("✏️", key=f"edit_mode_{row['task_id']}", help="Edit task properties"):
                    st.session_state.editing_task_id = row['task_id']
                    st.rerun()
            with btn_delete:
                if st.button("🗑️", key=f"delete_{row['task_id']}", help="Delete task permanently"):
                    # Remove the row where the task matches, save the spreadsheet, and refresh
                    df = df[df['task_id'] != row['task_id']]
                    save_db(df)
                    st.rerun()
    st.markdown("<hr style='margin:0.2em 0px; border-color:#f0f2f6;'>", unsafe_allowed_html=True)

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
