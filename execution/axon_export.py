#!/usr/bin/env python3
"""
AXON CSV Export Script
Generates billing-ready CSV in AXON B622 format from completed tickets.

Usage:
    python3 axon_export.py --export-all
    python3 axon_export.py --date-from 2026-01-01 --date-to 2026-01-07
    python3 axon_export.py --customer "Spur Petroleum Corp"
    python3 axon_export.py --tickets "260101001,260101002"
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# AXON B622 Column Order (CRITICAL - DO NOT CHANGE ORDER)
AXON_COLUMNS = [
    'Attachment',      # A - Always "FALSE"
    'Customer',        # B - Customer name
    'Location',        # C - "From to To" format
    'Start Date',      # D - DD-MM-YYYY HH:MM
    'Reference',       # E - Usually blank
    'Ticket#',         # F - YYMMDDXXX
    'Truck#',          # G - Unit number
    'Operator',        # H - "Last, First" format
    'Trailer#',        # I - Trailer ID
    'Product',         # J - Product type
    'Actual Vol',      # K - Decimal m³
    'Product2',        # L - Usually blank
    'From LSD',        # M - Pickup location
    'To LSD',          # N - Delivery location
    'Hours',           # O - Decimal hours
    'Charge',          # P - AR fills in
    'Job Desc',        # Q - "{Product} - {Customer}"
    'Company',         # R - "Rick's Oilfield Hauling"
    'Status',          # S - "Completed"
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Rick's TicketDrop 2.0"
COMPLETED_SHEET = "COMPLETED TICKETS"


def get_credentials():
    """Load Google credentials from service account or OAuth."""
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


def format_operator_name(driver_name: str) -> str:
    """Convert 'First Last' to 'Last, First' format."""
    parts = driver_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {parts[0]}"
    return driver_name


def format_start_date(timestamp: str) -> str:
    """Convert ISO timestamp to DD-MM-YYYY HH:MM format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return timestamp


def get_completed_tickets(
    client: gspread.Client,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    customer: Optional[str] = None,
    ticket_numbers: Optional[List[str]] = None,
    export_all: bool = False,
    force: bool = False
) -> List[Dict]:
    """Fetch completed tickets from Google Sheet with filters."""
    
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(COMPLETED_SHEET)
    except gspread.SpreadsheetNotFound:
        print(f"Error: Spreadsheet '{SPREADSHEET_NAME}' not found", file=sys.stderr)
        return []
    except gspread.WorksheetNotFound:
        print(f"Error: Worksheet '{COMPLETED_SHEET}' not found", file=sys.stderr)
        return []
    
    records = worksheet.get_all_records()
    filtered = []
    
    for row in records:
        # Skip if already exported (unless force)
        if not force and row.get('exported', '').upper() == 'Y':
            continue
        
        # Apply filters
        if ticket_numbers and row.get('ticket_number') not in ticket_numbers:
            continue
        
        if customer and row.get('customer', '').lower() != customer.lower():
            continue
        
        if date_from:
            ticket_date = row.get('date', '')
            if ticket_date < date_from:
                continue
        
        if date_to:
            ticket_date = row.get('date', '')
            if ticket_date > date_to:
                continue
        
        # Validate required fields
        if not row.get('actual_volume') or float(row.get('actual_volume', 0)) <= 0:
            print(f"Warning: Skipping ticket {row.get('ticket_number')} - zero volume")
            continue
        
        if not row.get('hours') or float(row.get('hours', 0)) <= 0:
            print(f"Warning: Skipping ticket {row.get('ticket_number')} - zero hours")
            continue
        
        filtered.append(row)
    
    return filtered


def transform_to_axon(ticket: Dict) -> Dict:
    """Transform ticket data to AXON B622 format."""
    
    from_lsd = ticket.get('from_lsd', '')
    to_lsd = ticket.get('to_lsd', '')
    product = ticket.get('product', '')
    customer = ticket.get('customer', '')
    
    return {
        'Attachment': 'FALSE',
        'Customer': customer,
        'Location': f"{from_lsd} to {to_lsd}",
        'Start Date': format_start_date(ticket.get('arrive_load', '')),
        'Reference': '',
        'Ticket#': ticket.get('ticket_number', ''),
        'Truck#': ticket.get('truck', ''),
        'Operator': format_operator_name(ticket.get('driver', '')),
        'Trailer#': ticket.get('trailer', ''),
        'Product': product,
        'Actual Vol': f"{float(ticket.get('actual_volume', 0)):.2f}",
        'Product2': '',
        'From LSD': from_lsd,
        'To LSD': to_lsd,
        'Hours': f"{float(ticket.get('hours', 0)):.2f}",
        'Charge': '',
        'Job Desc': f"{product} - {customer}",
        'Company': "Rick's Oilfield Hauling",
        'Status': 'Completed',
    }


def export_to_csv(tickets: List[Dict], output_path: str) -> str:
    """Write tickets to CSV file in AXON format."""
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=AXON_COLUMNS)
        writer.writeheader()
        
        for ticket in tickets:
            axon_row = transform_to_axon(ticket)
            writer.writerow(axon_row)
    
    return output_path


def mark_as_exported(client: gspread.Client, ticket_numbers: List[str], export_file: str):
    """Update tickets as exported in Google Sheet."""
    
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(COMPLETED_SHEET)
    except Exception as e:
        print(f"Error marking exported: {e}", file=sys.stderr)
        return
    
    records = worksheet.get_all_records()
    headers = worksheet.row_values(1)
    
    exported_col = headers.index('exported') + 1 if 'exported' in headers else None
    exported_at_col = headers.index('exported_at') + 1 if 'exported_at' in headers else None
    export_file_col = headers.index('export_file') + 1 if 'export_file' in headers else None
    ticket_col = headers.index('ticket_number') + 1 if 'ticket_number' in headers else 1
    
    now = datetime.now().isoformat()
    
    for i, row in enumerate(records, start=2):  # Start at row 2 (after header)
        if row.get('ticket_number') in ticket_numbers:
            if exported_col:
                worksheet.update_cell(i, exported_col, 'Y')
            if exported_at_col:
                worksheet.update_cell(i, exported_at_col, now)
            if export_file_col:
                worksheet.update_cell(i, export_file_col, export_file)


def main():
    parser = argparse.ArgumentParser(description="Export completed tickets to AXON CSV format")
    parser.add_argument("--date-from", help="Start date filter (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="End date filter (YYYY-MM-DD)")
    parser.add_argument("--customer", help="Filter by customer name")
    parser.add_argument("--tickets", help="Comma-separated ticket numbers")
    parser.add_argument("--export-all", action="store_true", help="Export all unexported tickets")
    parser.add_argument("--force", action="store_true", help="Re-export already exported tickets")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--no-mark", action="store_true", help="Don't mark tickets as exported")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.date_from, args.date_to, args.customer, args.tickets, args.export_all]):
        print("Error: Must specify at least one filter or --export-all", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # Authenticate
    creds = get_credentials()
    if not creds:
        print("Error: Could not load Google credentials", file=sys.stderr)
        sys.exit(1)
    
    client = gspread.authorize(creds)
    
    # Parse ticket numbers
    ticket_numbers = None
    if args.tickets:
        ticket_numbers = [t.strip() for t in args.tickets.split(',')]
    
    # Fetch tickets
    tickets = get_completed_tickets(
        client,
        date_from=args.date_from,
        date_to=args.date_to,
        customer=args.customer,
        ticket_numbers=ticket_numbers,
        export_all=args.export_all,
        force=args.force
    )
    
    if not tickets:
        print("No tickets to export")
        sys.exit(0)
    
    print(f"Found {len(tickets)} tickets to export")
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f".tmp/AXON_Export_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    
    # Export to CSV
    export_to_csv(tickets, output_file)
    print(f"Exported to: {output_file}")
    
    # Mark as exported
    if not args.no_mark:
        exported_numbers = [t.get('ticket_number') for t in tickets]
        mark_as_exported(client, exported_numbers, os.path.basename(output_file))
        print(f"Marked {len(exported_numbers)} tickets as exported")
    
    print("\nExport complete!")
    print(f"Copy to AXON import folder: C:\\AxonETAAttach\\{os.path.basename(output_file)}")


if __name__ == "__main__":
    main()
