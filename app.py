import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. Page Configuration (This styles your browser window)
st.set_page_config(page_title="My Personal Tracker", layout="wide")

# 2. Database File Setup
DB_FILE = "tasks_db.csv"

# 3. Check if your data file exists. If not, create a starter database.
if not os.path.exists(DB_FILE):
    # This creates starter tasks so you can see how the app works immediately
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
    # If the file already exists, open it up!
    df = pd.read_csv(DB_FILE)

# 4. Helper function to save changes to our file
def save_db(dataframe):
    dataframe.to_csv(DB_FILE, index=False)

# 5. Application UI Header
st.title("🗓️ My Personal Tracker & Scheduler")
st.markdown("---")
# --- PART 3: MASTER SCHEDULE VIEW ---
st.subheader("📋 Master Schedule Overview")

# Create a copy of our data to format nicely for the screen
df_display = df.copy()
df_display['Last Completed'] = pd.to_datetime(df_display['last_completed']).dt.date

# Calculate future due dates based on intervals (7 days or 30 days)
next_dues = []
for index, row in df_display.iterrows():
    if row['frequency'] == "Weekly":
        next_dues.append(row['Last Completed'] + timedelta(days=7))
    else:
        next_dues.append(row['Last Completed'] + timedelta(days=30))
        
df_display['Next Due Date'] = next_dues

# Render the interactive clean data table grid
st.dataframe(
    df_display[['task_name', 'frequency', 'Last Completed', 'Next Due Date']],
    use_container_width=True,
    hide_index=True
)

# --- PART 4: CREATE NEW ITEMS ---
st.markdown("---")
st.subheader("➕ Add Custom Recurring Task")

# Build a clean input form
with st.form("new_task_form", clear_on_submit=True):
    new_name = st.text_input("Task Description")
    new_freq = st.selectbox("Interval Cycle", ["Weekly", "Monthly"])
    submitted = st.form_submit_with_button("Create Entry")
    
    if submitted and new_name:
        # Calculate the next ID number sequentially
        new_id = df['task_id'].max() + 1 if not df.empty else 1
        
        # Set default completion to the past so it triggers an alert immediately upon creation
        default_past = today - timedelta(days=8 if new_freq == "Weekly" else 32)
        
        new_row = {
            "task_id": new_id,
            "task_name": new_name,
            "frequency": new_freq,
            "last_completed": default_past.strftime("%Y-%m-%d")
        }
        
        # Add the new row to our existing list and save it to our database file
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_db(df)
        st.success(f"Successfully added: {new_name}")
        st.rerun()
