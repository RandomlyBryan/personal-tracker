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