import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. Page Configuration
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database File Setup
DB_FILE = "tasks_db.csv"

# Load existing tasks or initialize defaults
if not os.path.exists(DB_FILE):
    starter_data = {
        "task_id": [1, 2],
        "task_name": ["Weekly Tracker Maintenance", "Monthly Budget Check-in"],
        "frequency": ["Weekly", "Monthly"],
        "last_completed": [
            (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"), 
            (datetime.now() - timedelta(days=32)).strftime("%Y-%m-%d")
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
    last_comp_date = datetime.strptime(str(row['last_completed']), "%Y-%m-%d").date()
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
            if st.button("Mark Completed", key=f"btn_{row['task_id']}"):
                df.at[index, 'last_completed'] = today.strftime("%Y-%m-%d")
                save_db(df)
                st.rerun()

if not reminders_found:
    st.success("All clear! Your recurring tasks are up to date.")

st.markdown("---")

# --- PART 3: MASTER SCHEDULE VIEW ---
st.subheader("📋 Master Schedule Overview")

df_display = df.copy()
df_display['Last Completed'] = pd.to_datetime(df_display['last_completed']).dt.date

next_dues = []
for index, row in df_display.iterrows():
    if row['frequency'] == "Weekly":
        next_dues.append(row['Last Completed'] + timedelta(days=7))
    else:
        next_dues.append(row['Last Completed'] + timedelta(days=30))
        
df_display['Next Due Date'] = next_dues

st.dataframe(
    df_display[['task_name', 'frequency', 'Last Completed', 'Next Due Date']],
    use_container_width=True,
    hide_index=True
)

# --- PART 4: CREATE NEW ITEMS ---
st.markdown("---")
st.subheader("➕ Add Custom Recurring Task")

with st.form("new_task_form", clear_on_submit=True):
    new_name = st.text_input("Task Description")
    new_freq = st.selectbox("Interval Cycle", ["Weekly", "Monthly"])
    # FIXED LINE BELOW: Changed form_submit_with_button to form_submit_button
    submitted = st.form_submit_button("Create Entry")
    
    if submitted and new_name:
        new_id = df['task_id'].max() + 1 if not df.empty else 1
        default_past = today - timedelta(days=8 if new_freq == "Weekly" else 32)
        
        new_row = {
            "task_id": new_id,
            "task_name": new_name,
            "frequency": new_freq,
            "last_completed": default_past.strftime("%Y-%m-%d")
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_db(df)
        st.success(f"Successfully added: {new_name}")
        st.rerun()
