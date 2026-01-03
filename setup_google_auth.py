#!/usr/bin/env python3
"""
Google Authentication Setup for TicketDrop 2.0
Run this first to set up your Google Sheets connection.

Usage:
    python3 setup_google_auth.py
"""

import os
import sys
import json

def check_credentials():
    """Check what credentials are available."""
    print("\n" + "="*60)
    print("TicketDrop 2.0 - Google Authentication Setup")
    print("="*60 + "\n")
    
    # Check for service account
    if os.path.exists('service_account.json'):
        print("✓ Found: service_account.json")
        try:
            with open('service_account.json', 'r') as f:
                data = json.load(f)
                email = data.get('client_email', 'unknown')
                print(f"  Service Account Email: {email}")
                print(f"\n  ⚠️  IMPORTANT: Share your Google Sheet with this email!")
                print(f"     Copy this email and add it as an Editor to your sheet.")
            return True
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            return False
    
    # Check for OAuth token
    if os.path.exists('token.json'):
        print("✓ Found: token.json (OAuth credentials)")
        print("  You're authenticated via OAuth.")
        return True
    
    # Check for OAuth credentials file
    if os.path.exists('credentials.json'):
        print("✓ Found: credentials.json (OAuth client)")
        print("  Run the scripts - they'll open a browser to authenticate.")
        return True
    
    # Nothing found
    print("✗ No credentials found!\n")
    print("You need ONE of these options:\n")
    
    print("OPTION 1: Service Account (Recommended for automation)")
    print("-" * 50)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a project (or select existing)")
    print("3. Enable 'Google Sheets API' and 'Google Drive API'")
    print("4. Go to: IAM & Admin → Service Accounts")
    print("5. Create a service account")
    print("6. Click on it → Keys tab → Add Key → Create new key → JSON")
    print("7. Download the JSON file")
    print("8. RENAME it to: service_account.json")
    print("9. PUT it in this folder:", os.getcwd())
    print("10. Share your Google Sheet with the service account email\n")
    
    print("OPTION 2: OAuth (Easier for personal use)")
    print("-" * 50)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a project (or select existing)")
    print("3. Enable 'Google Sheets API' and 'Google Drive API'")
    print("4. Go to: APIs & Services → Credentials")
    print("5. Create Credentials → OAuth client ID → Desktop app")
    print("6. Download the JSON")
    print("7. RENAME it to: credentials.json")
    print("8. PUT it in this folder:", os.getcwd())
    print("9. Run the scripts - browser will open to authorize\n")
    
    return False


def test_connection():
    """Try to connect to Google Sheets."""
    print("\nTesting connection...")
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("✗ Missing dependencies. Run: pip install gspread google-auth google-auth-oauthlib")
        return False
    
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = None
    
    # Try service account
    if os.path.exists('service_account.json'):
        try:
            creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
            print("✓ Service account credentials loaded")
        except Exception as e:
            print(f"✗ Service account error: {e}")
    
    # Try OAuth token
    elif os.path.exists('token.json'):
        try:
            from google.oauth2.credentials import Credentials as UserCredentials
            creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)
            print("✓ OAuth credentials loaded")
        except Exception as e:
            print(f"✗ OAuth token error: {e}")
    
    # Try OAuth flow
    elif os.path.exists('credentials.json'):
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save for next time
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("✓ OAuth flow completed, token saved")
        except Exception as e:
            print(f"✗ OAuth flow error: {e}")
    
    if not creds:
        print("✗ No valid credentials")
        return False
    
    # Try to access Google Sheets
    try:
        client = gspread.authorize(creds)
        print("✓ Connected to Google Sheets API")
        
        # Try to find the spreadsheet
        spreadsheet_name = "Rick's TicketDrop 2.0"
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"✓ Found spreadsheet: {spreadsheet_name}")
            print(f"  URL: {spreadsheet.url}")
            
            # List sheets
            sheets = [ws.title for ws in spreadsheet.worksheets()]
            print(f"  Tabs: {', '.join(sheets)}")
            
            return True
        except gspread.SpreadsheetNotFound:
            print(f"✗ Spreadsheet '{spreadsheet_name}' not found")
            print(f"\n  Either:")
            print(f"  1. Create a Google Sheet named exactly: {spreadsheet_name}")
            print(f"  2. OR share your existing sheet with the service account email")
            return False
            
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False


def main():
    if check_credentials():
        test_connection()
    
    print("\n" + "="*60)
    print("Need help? Common issues:")
    print("="*60)
    print("• 'File not found' → Put credentials file in:", os.getcwd())
    print("• 'Permission denied' → Share sheet with service account email")
    print("• 'API not enabled' → Enable Sheets & Drive APIs in Google Cloud")
    print("• 'Spreadsheet not found' → Name must be exactly: Rick's TicketDrop 2.0")
    print("")


if __name__ == "__main__":
    main()
