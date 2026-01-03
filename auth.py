import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_google_client():
    creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    return gspread.authorize(creds)

def get_spreadsheet():
    return get_google_client().open("Rick's TicketDrop 2.0")
