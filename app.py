import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
# ... (keep other imports)

# 1. Page Configuration & CSS
st.set_page_config(page_title="Personal Task Tracker", layout="wide")

# CSS: Reinforced Calendar Unwrapping
st.markdown(
    """
    <style>
        /* Force Calendar Containers to be fluid height and wrap text */
        .fc .fc-daygrid-event {
            white-space: normal !important;
            height: auto !important;
            word-wrap: break-word !important;
        }
        .fc-event-main, .fc-event-title {
            white-space: normal !important;
            overflow: visible !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ... (Include your database initialization block here)

# 2. Define Calendar Options BEFORE calling the calendar component
calendar_options = {
    "initialView": "dayGridMonth", 
    "headerToolbar": { "left": "prev,next today", "center": "title", "right": "" }, 
    "editable": False, 
    "selectable": True, 
    "height": "auto", 
    "dayMaxEvents": True, # This handles the "More" link for long days
}

# 3. Call the calendar component now that options is defined
calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
