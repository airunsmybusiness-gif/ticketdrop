#!/usr/bin/env python3
"""
Ticket Creation Script
Creates new field tickets in the DISPATCH BOARD sheet.

Usage:
    python3 create_ticket.py --customer "Spur Petroleum Corp" --from-lsd "10-15-052-20W4" ...
    python3 create_ticket.py --batch tickets.csv
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Rick's TicketDrop 2.0"
DISPATCH_SHEET = "DISPATCH BOARD"
ACTIVE_SHEET = "ACTIVE TICKETS"
SETTINGS_SHEET = "SETTINGS"


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


def load_settings(client: gspread.Client) -> Dict[str, List[str]]:
    """Load validation lists from SETTINGS sheet."""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(SETTINGS_SHEET)
        
        data = worksheet.get_all_values()
        if not data:
            return {}
        
        settings = {}
        headers = data[0]
        
        for col_idx, header in enumerate(headers):
            values = [row[col_idx] for row in data[1:] if len(row) > col_idx and row[col_idx]]
            settings[header.upper()] = values
        
        return settings
    
    except Exception as e:
        print(f"Warning: Could not load settings: {e}", file=sys.stderr)
        return {}


def generate_ticket_number(client: gspread.Client) -> str:
    """Generate next ticket number in YYMMDDXXX format."""
    today = datetime.now()
    prefix = today.strftime("%y%m%d")
    
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # Check both DISPATCH and ACTIVE sheets for today's tickets
        existing_numbers = []
        
        for sheet_name in [DISPATCH_SHEET, ACTIVE_SHEET, "COMPLETED TICKETS"]:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                records = worksheet.get_all_records()
                
                for row in records:
                    ticket_num = str(row.get('ticket_number', ''))
                    if ticket_num.startswith(prefix):
                        existing_numbers.append(ticket_num)
            except:
                continue
        
        # Find next sequence number
        if not existing_numbers:
            sequence = 1
        else:
            sequences = [int(num[-3:]) for num in existing_numbers if len(num) == 9]
            sequence = max(sequences) + 1 if sequences else 1
        
        return f"{prefix}{sequence:03d}"
    
    except Exception as e:
        print(f"Warning: Could not check existing tickets: {e}", file=sys.stderr)
        return f"{prefix}001"


def validate_ticket(ticket_data: Dict, settings: Dict) -> List[str]:
    """Validate ticket data against settings."""
    errors = []
    
    # Required fields
    required = ['customer', 'from_lsd', 'to_lsd', 'product', 'driver', 'truck']
    for field in required:
        if not ticket_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate against settings lists
    if settings.get('CUSTOMERS'):
        if ticket_data.get('customer') and ticket_data['customer'] not in settings['CUSTOMERS']:
            errors.append(f"Unknown customer: {ticket_data['customer']}")
    
    if settings.get('DRIVERS'):
        if ticket_data.get('driver') and ticket_data['driver'] not in settings['DRIVERS']:
            errors.append(f"Unknown driver: {ticket_data['driver']}")
    
    if settings.get('PRODUCTS'):
        if ticket_data.get('product') and ticket_data['product'] not in settings['PRODUCTS']:
            errors.append(f"Unknown product: {ticket_data['product']}")
    
    if settings.get('TRUCKS'):
        if ticket_data.get('truck') and ticket_data['truck'] not in settings['TRUCKS']:
            errors.append(f"Unknown truck: {ticket_data['truck']}")
    
    if settings.get('TRAILERS'):
        if ticket_data.get('trailer') and ticket_data['trailer'] not in settings['TRAILERS']:
            errors.append(f"Unknown trailer: {ticket_data['trailer']}")
    
    return errors


def create_ticket(client: gspread.Client, ticket_data: Dict, settings: Dict) -> Dict:
    """Create a new ticket in the DISPATCH BOARD."""
    
    # Validate
    errors = validate_ticket(ticket_data, settings)
    if errors:
        return {"success": False, "errors": errors}
    
    # Generate ticket number
    ticket_number = generate_ticket_number(client)
    
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(DISPATCH_SHEET)
        
        # Prepare row data
        now = datetime.now()
        row = [
            "",  # A: Create checkbox (empty)
            ticket_number,  # B: Ticket#
            now.strftime("%Y-%m-%d"),  # C: Date
            ticket_data.get('customer', ''),  # D: Customer
            ticket_data.get('from_lsd', ''),  # E: From LSD
            ticket_data.get('to_lsd', ''),  # F: To LSD
            ticket_data.get('product', ''),  # G: Product
            ticket_data.get('driver', ''),  # H: Driver
            ticket_data.get('truck', ''),  # I: Truck
            ticket_data.get('trailer', ''),  # J: Trailer
            ticket_data.get('est_volume', ''),  # K: Est Vol
            ticket_data.get('special_instructions', ''),  # L: Instructions
            ticket_data.get('priority', 'Normal'),  # M: Priority
        ]
        
        # Append row
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        
        return {
            "success": True,
            "ticket_number": ticket_number,
            "message": f"Ticket {ticket_number} created successfully"
        }
    
    except Exception as e:
        return {"success": False, "errors": [str(e)]}


def create_tickets_batch(client: gspread.Client, csv_file: str, settings: Dict) -> Dict:
    """Create multiple tickets from CSV file."""
    results = {"created": [], "failed": []}
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                result = create_ticket(client, row, settings)
                
                if result.get('success'):
                    results['created'].append(result['ticket_number'])
                else:
                    results['failed'].append({
                        "data": row,
                        "errors": result.get('errors', [])
                    })
    
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    return {
        "success": True,
        "created_count": len(results['created']),
        "failed_count": len(results['failed']),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="Create field tickets")
    
    # Single ticket mode
    parser.add_argument("--customer", help="Customer name")
    parser.add_argument("--from-lsd", help="Pickup location")
    parser.add_argument("--to-lsd", help="Delivery location")
    parser.add_argument("--product", help="Product type")
    parser.add_argument("--driver", help="Driver name")
    parser.add_argument("--truck", help="Truck unit number")
    parser.add_argument("--trailer", help="Trailer ID")
    parser.add_argument("--est-volume", help="Estimated volume (m³)")
    parser.add_argument("--instructions", help="Special instructions")
    parser.add_argument("--priority", default="Normal", help="Priority level")
    
    # Batch mode
    parser.add_argument("--batch", help="CSV file for batch creation")
    
    # Output
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    # Authenticate
    creds = get_credentials()
    if not creds:
        print("Error: Could not load Google credentials", file=sys.stderr)
        sys.exit(1)
    
    client = gspread.authorize(creds)
    
    # Load settings
    settings = load_settings(client)
    
    if args.batch:
        # Batch mode
        result = create_tickets_batch(client, args.batch, settings)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Created: {result.get('created_count', 0)}")
            print(f"Failed: {result.get('failed_count', 0)}")
            
            if result.get('results', {}).get('failed'):
                print("\nFailed tickets:")
                for fail in result['results']['failed']:
                    print(f"  - {fail['data']}: {fail['errors']}")
    else:
        # Single ticket mode
        if not args.customer:
            print("Error: --customer required for single ticket creation", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        ticket_data = {
            'customer': args.customer,
            'from_lsd': args.from_lsd,
            'to_lsd': args.to_lsd,
            'product': args.product,
            'driver': args.driver,
            'truck': args.truck,
            'trailer': args.trailer,
            'est_volume': args.est_volume,
            'special_instructions': args.instructions,
            'priority': args.priority,
        }
        
        result = create_ticket(client, ticket_data, settings)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get('success'):
                print(f"✓ Ticket created: {result['ticket_number']}")
            else:
                print("✗ Failed to create ticket:")
                for error in result.get('errors', []):
                    print(f"  - {error}")
                sys.exit(1)


if __name__ == "__main__":
    main()
