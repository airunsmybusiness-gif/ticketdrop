"""
auth.py - Google Sheets Authentication for TicketDrop 2.0
"""

import gspread
import streamlit as st
import os
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_client():
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if 'private_key' in creds_dict:
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    elif os.path.exists('service_account.json'):
        credentials = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    else:
        raise FileNotFoundError("No Google credentials found")
    
    return gspread.authorize(credentials)

def get_spreadsheet(spreadsheet_name="Rick's TicketDrop 2.0"):
    client = get_google_client()
    return client.open(spreadsheet_name)

def get_worksheet(sheet_name, spreadsheet_name="Rick's TicketDrop 2.0"):
    spreadsheet = get_spreadsheet(spreadsheet_name)
    return spreadsheet.worksheet(sheet_name)
