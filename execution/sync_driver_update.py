#!/usr/bin/env python3
"""
Sync Driver Update Script
Handles updates from the mobile driver app to Google Sheets.

Usage:
    python3 sync_driver_update.py --ticket "260101001" --field "arrive_load" --value "2026-01-01T08:30:00"
    python3 sync_driver_update.py --complete --ticket "260101001" --data '{"actual_volume": 85.5, ...}'
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Rick's TicketDrop 2.0"
ACTIVE_SHEET = "ACTIVE TICKETS"
COMPLETED_SHEET = "COMPLETED TICKETS"


def get_credentials():
    """Load Google credentials."""
    creds = None
    
    if os.path.exists('token.json'):
        from google.oauth2.credentials import Credentials as UserCredentials
        creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
    
    if not creds:
        service_account_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
        if os.path.exists(service_account_file):
            creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    
    return creds


def find_ticket_row(worksheet: gspread.Worksheet, ticket_number: str) -> Optional[int]:
    """Find the row number for a ticket."""
    records = worksheet.get_all_records()
    headers = worksheet.row_values(1)
    
    ticket_col = 'ticket_number' if 'ticket_number' in headers else 'Ticket#'
    
    for i, row in enumerate(records, start=2):  # Row 2 is first data row
        if str(row.get(ticket_col, row.get('ticket_number', ''))) == str(ticket_number):
            return i
    
    return None


def update_field(client: gspread.Client, ticket_number: str, field: str, value: str) -> Dict:
    """Update a single field on a ticket."""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(ACTIVE_SHEET)
        
        # Find ticket row
        row_num = find_ticket_row(worksheet, ticket_number)
        if not row_num:
            return {"success": False, "error": f"Ticket {ticket_number} not found"}
        
        # Find column
        headers = worksheet.row_values(1)
        if field not in headers:
            # Try alternate names
            field_map = {
                'arrive_load': 'Arrive Load',
                'depart_load': 'Depart Load',
                'arrive_offload': 'Arrive Offload',
                'depart_offload': 'Depart Offload',
                'actual_volume': 'Actual Vol',
            }
            field = field_map.get(field, field)
        
        if field not in headers:
            return {"success": False, "error": f"Field '{field}' not found in sheet"}
        
        col_num = headers.index(field) + 1
        
        # Update cell
        worksheet.update_cell(row_num, col_num, value)
        
        # Update timestamp
        if 'updated_at' in headers or 'Updated At' in headers:
            update_col = headers.index('updated_at' if 'updated_at' in headers else 'Updated At') + 1
            worksheet.update_cell(row_num, update_col, datetime.now().isoformat())
        
        # Update status if first timestamp
        if field in ['arrive_load', 'Arrive Load']:
            if 'status' in headers or 'Status' in headers:
                status_col = headers.index('status' if 'status' in headers else 'Status') + 1
                worksheet.update_cell(row_num, status_col, 'IN_PROGRESS')
        
        return {
            "success": True,
            "ticket_number": ticket_number,
            "field": field,
            "value": value
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_hours(data: Dict) -> float:
    """Calculate total hours from timestamps."""
    try:
        arrive = datetime.fromisoformat(data.get('arrive_load', '').replace('Z', '+00:00'))
        depart = datetime.fromisoformat(data.get('depart_offload', '').replace('Z', '+00:00'))
        delta = depart - arrive
        return round(delta.total_seconds() / 3600, 2)
    except:
        return 0.0


def calculate_wait_time(data: Dict) -> float:
    """Calculate wait time from timestamps."""
    try:
        arrive1 = datetime.fromisoformat(data.get('arrive_load', '').replace('Z', '+00:00'))
        depart1 = datetime.fromisoformat(data.get('depart_load', '').replace('Z', '+00:00'))
        arrive2 = datetime.fromisoformat(data.get('arrive_offload', '').replace('Z', '+00:00'))
        depart2 = datetime.fromisoformat(data.get('depart_offload', '').replace('Z', '+00:00'))
        
        wait1 = (depart1 - arrive1).total_seconds() / 3600
        wait2 = (depart2 - arrive2).total_seconds() / 3600
        
        return round(wait1 + wait2, 2)
    except:
        return 0.0


def complete_ticket(client: gspread.Client, ticket_number: str, data: Dict) -> Dict:
    """Complete a ticket and move to COMPLETED TICKETS."""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        active_ws = spreadsheet.worksheet(ACTIVE_SHEET)
        completed_ws = spreadsheet.worksheet(COMPLETED_SHEET)
        
        # Find ticket row
        row_num = find_ticket_row(active_ws, ticket_number)
        if not row_num:
            return {"success": False, "error": f"Ticket {ticket_number} not found"}
        
        # Get current row data
        row_values = active_ws.row_values(row_num)
        headers = active_ws.row_values(1)
        ticket_data = dict(zip(headers, row_values))
        
        # Calculate derived fields
        data['hours'] = data.get('hours') or calculate_hours(data)
        data['wait_time'] = data.get('wait_time') or calculate_wait_time(data)
        data['status'] = 'COMPLETED'
        data['completed_at'] = datetime.now().isoformat()
        
        # Merge driver data with existing ticket data
        for key, value in data.items():
            ticket_data[key] = value
        
        # Prepare row for completed sheet
        completed_headers = completed_ws.row_values(1)
        completed_row = [ticket_data.get(h, '') for h in completed_headers]
        
        # Append to COMPLETED TICKETS
        completed_ws.append_row(completed_row, value_input_option='USER_ENTERED')
        
        # Delete from ACTIVE TICKETS
        active_ws.delete_rows(row_num)
        
        return {
            "success": True,
            "ticket_number": ticket_number,
            "status": "COMPLETED",
            "hours": data['hours'],
            "message": f"Ticket {ticket_number} completed and moved to billing"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Sync driver updates to Google Sheets")
    parser.add_argument("--ticket", required=True, help="Ticket number")
    parser.add_argument("--field", help="Field to update")
    parser.add_argument("--value", help="New value")
    parser.add_argument("--complete", action="store_true", help="Complete the ticket")
    parser.add_argument("--data", help="JSON data for completion")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    # Authenticate
    creds = get_credentials()
    if not creds:
        print("Error: Could not load Google credentials", file=sys.stderr)
        sys.exit(1)
    
    client = gspread.authorize(creds)
    
    if args.complete:
        # Complete ticket
        data = json.loads(args.data) if args.data else {}
        result = complete_ticket(client, args.ticket, data)
    else:
        # Update single field
        if not args.field or not args.value:
            print("Error: --field and --value required for update", file=sys.stderr)
            sys.exit(1)
        
        result = update_field(client, args.ticket, args.field, args.value)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get('success'):
            print(f"✓ {result.get('message', 'Update successful')}")
        else:
            print(f"✗ Error: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
