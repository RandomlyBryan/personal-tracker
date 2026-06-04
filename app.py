import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
import base64
import requests
from streamlit_calendar import calendar
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Personal Task Tracker", layout="wide")

# CSS: Reinforced Calendar Unwrapping
st.markdown(
    """
    <style>
        /* Force Calendar Containers to be fluid height */
        .fc .fc-daygrid-event {
            white-space: normal !important;
            height: auto !important;
        }
        .fc-event-main {
            white-space: normal !important;
        }
        .fc-event-title {
            white-space: normal !important;
        }
        /* Ensure the Daygrid row grows with content */
        .fc-daygrid-body, .fc-scrollgrid-sync-table {
            height: auto !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ... (Keep your existing data loading, database checks, and helper functions)

# --- REVISED CALENDAR BLOCK ---
# Using a simpler options dictionary to avoid the string-execution error
calendar_options = {
    "initialView": "dayGridMonth", 
    "headerToolbar": { "left": "prev,next today", "center": "title", "right": "" }, 
    "editable": False, 
    "selectable": True, 
    "height": "auto", 
    "dayMaxEvents": True,
}

calendar(events=calendar_events, options=calendar_options, key="monthly_grid_view")
