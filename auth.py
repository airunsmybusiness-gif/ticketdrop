"""
TicketDrop 2.0 - Shared Authentication
Works both locally (service_account.json) and on Streamlit Cloud (secrets)
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_client():
    """
    Get authenticated Google client.
    Works with both local file and Streamlit Cloud secrets.
    """
    
    # Try Streamlit Cloud secrets first
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    
    # Fall back to local file
    if os.path.exists('service_account.json'):
        creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
        return gspread.authorize(creds)
    
    # Error
    st.error("❌ No credentials found! Add service_account.json or configure Streamlit secrets.")
    st.stop()

def get_spreadsheet():
    """Get the TicketDrop spreadsheet."""
    client = get_google_client()
    return client.open("Rick's TicketDrop 2.0")
