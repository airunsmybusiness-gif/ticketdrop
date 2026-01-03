#!/usr/bin/env python3
"""
Ticket Validation Script
Validates ticket data at creation, completion, and export stages.

Usage:
    python3 validate_ticket.py --ticket "260101001"
    python3 validate_ticket.py --stage creation
    python3 validate_ticket.py --stage export
    python3 validate_ticket.py --report
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Rick's TicketDrop 2.0"


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


def validate_lsd(value: str) -> Tuple[bool, Optional[str]]:
    """Validate LSD format or accept lease names."""
    if not value or not value.strip():
        return False, "Location required"
    
    value = value.strip()
    
    # Standard LSD pattern: XX-XX-XXX-XXW5
    lsd_pattern = r'^\d{1,2}-\d{1,2}-\d{1,3}-\d{1,2}W\d$'
    if re.match(lsd_pattern, value):
        return True, None
    
    # Accept any string >= 2 chars as lease name
    if len(value) >= 2:
        return True, None
    
    return False, "Invalid location format"


def validate_timestamps(data: Dict) -> List[str]:
    """Validate timestamp sequence and logic."""
    errors = []
    
    timestamps = {}
    for field in ['arrive_load', 'depart_load', 'arrive_offload', 'depart_offload']:
        value = data.get(field, '')
        if value:
            try:
                timestamps[field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Invalid timestamp format: {field}")
    
    if len(errors) > 0:
        return errors
    
    # Check sequence
    if 'depart_load' in timestamps and 'arrive_load' in timestamps:
        if timestamps['depart_load'] <= timestamps['arrive_load']:
            errors.append("Departed pickup before arriving")
    
    if 'arrive_offload' in timestamps and 'depart_load' in timestamps:
        if timestamps['arrive_offload'] <= timestamps['depart_load']:
            errors.append("Arrived at delivery before leaving pickup")
    
    if 'depart_offload' in timestamps and 'arrive_offload' in timestamps:
        if timestamps['depart_offload'] <= timestamps['arrive_offload']:
            errors.append("Departed delivery before arriving")
    
    # Check for unreasonably long times
    if 'arrive_load' in timestamps and 'depart_offload' in timestamps:
        total_hours = (timestamps['depart_offload'] - timestamps['arrive_load']).total_seconds() / 3600
        if total_hours > 24:
            errors.append(f"Total time exceeds 24 hours ({total_hours:.1f}h)")
    
    return errors


def validate_volume(actual_volume: float, est_volume: Optional[float] = None) -> Tuple[List[str], List[str]]:
    """Validate volume values."""
    errors = []
    warnings = []
    
    if actual_volume <= 0:
        errors.append("Volume must be greater than 0")
    
    if actual_volume > 500:
        warnings.append(f"Volume {actual_volume} m³ seems high - please verify")
    
    if est_volume and est_volume > 0:
        diff_pct = abs(actual_volume - est_volume) / est_volume
        if diff_pct > 0.20:
            warnings.append(f"Actual differs from estimated by {diff_pct*100:.0f}%")
    
    return errors, warnings


def validate_creation(data: Dict, settings: Dict) -> Dict:
    """Validate ticket at creation stage."""
    errors = []
    warnings = []
    
    # Required fields
    required = ['customer', 'from_lsd', 'to_lsd', 'product', 'driver', 'truck']
    for field in required:
        if not data.get(field):
            errors.append({"field": field, "message": f"Required field: {field}"})
    
    # Validate against settings
    if settings.get('CUSTOMERS'):
        if data.get('customer') and data['customer'] not in settings['CUSTOMERS']:
            errors.append({"field": "customer", "message": f"Unknown customer: {data['customer']}"})
    
    if settings.get('DRIVERS'):
        if data.get('driver') and data['driver'] not in settings['DRIVERS']:
            errors.append({"field": "driver", "message": f"Unknown driver: {data['driver']}"})
    
    if settings.get('PRODUCTS'):
        if data.get('product') and data['product'] not in settings['PRODUCTS']:
            errors.append({"field": "product", "message": f"Unknown product: {data['product']}"})
    
    if settings.get('TRUCKS'):
        if data.get('truck') and data['truck'] not in settings['TRUCKS']:
            errors.append({"field": "truck", "message": f"Unknown truck: {data['truck']}"})
    
    # Validate LSDs
    for field in ['from_lsd', 'to_lsd']:
        if data.get(field):
            valid, msg = validate_lsd(data[field])
            if not valid:
                errors.append({"field": field, "message": msg})
    
    return {
        "stage": "creation",
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_completion(data: Dict) -> Dict:
    """Validate ticket at completion stage."""
    errors = []
    warnings = []
    
    # Required timestamps
    required_timestamps = ['arrive_load', 'depart_load', 'arrive_offload', 'depart_offload']
    for field in required_timestamps:
        if not data.get(field):
            errors.append({"field": field, "message": f"Required timestamp: {field}"})
    
    # Validate timestamp logic
    ts_errors = validate_timestamps(data)
    for err in ts_errors:
        errors.append({"field": "timestamps", "message": err})
    
    # Required volume
    actual_vol = float(data.get('actual_volume', 0) or 0)
    vol_errors, vol_warnings = validate_volume(
        actual_vol,
        float(data.get('est_volume', 0) or 0)
    )
    for err in vol_errors:
        errors.append({"field": "actual_volume", "message": err})
    for warn in vol_warnings:
        warnings.append({"field": "actual_volume", "message": warn})
    
    # Required hazard check and signature
    if not data.get('hazard_check') or data.get('hazard_check', '').upper() != 'Y':
        errors.append({"field": "hazard_check", "message": "Hazard assessment required"})
    
    if not data.get('signature') or data.get('signature', '').upper() != 'Y':
        errors.append({"field": "signature", "message": "Driver signature required"})
    
    return {
        "stage": "completion",
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_export(data: Dict) -> Dict:
    """Validate ticket at export stage."""
    errors = []
    warnings = []
    
    # Must be completed
    if data.get('status', '').upper() != 'COMPLETED':
        errors.append({"field": "status", "message": "Only completed tickets can be exported"})
    
    # Required fields for AXON
    if not data.get('actual_volume') or float(data.get('actual_volume', 0)) <= 0:
        errors.append({"field": "actual_volume", "message": "Cannot export ticket with zero volume"})
    
    if not data.get('hours') or float(data.get('hours', 0)) <= 0:
        errors.append({"field": "hours", "message": "Cannot export ticket with zero hours"})
    
    if not data.get('arrive_load'):
        errors.append({"field": "arrive_load", "message": "Invalid arrival timestamp"})
    
    return {
        "stage": "export",
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def load_settings(client: gspread.Client) -> Dict:
    """Load settings from Google Sheet."""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("SETTINGS")
        
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


def validate_tickets_batch(client: gspread.Client, stage: str, settings: Dict) -> Dict:
    """Validate all tickets at a given stage."""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        sheet_map = {
            'creation': 'DISPATCH BOARD',
            'completion': 'ACTIVE TICKETS',
            'export': 'COMPLETED TICKETS'
        }
        
        worksheet = spreadsheet.worksheet(sheet_map.get(stage, 'ACTIVE TICKETS'))
        records = worksheet.get_all_records()
        
        results = {'passed': [], 'failed': [], 'warnings': []}
        
        for row in records:
            ticket_num = row.get('ticket_number', row.get('Ticket#', 'unknown'))
            
            if stage == 'creation':
                result = validate_creation(row, settings)
            elif stage == 'completion':
                result = validate_completion(row)
            else:
                result = validate_export(row)
            
            result['ticket_number'] = ticket_num
            
            if result['valid']:
                results['passed'].append(ticket_num)
                if result.get('warnings'):
                    results['warnings'].append({
                        'ticket_number': ticket_num,
                        'warnings': result['warnings']
                    })
            else:
                results['failed'].append({
                    'ticket_number': ticket_num,
                    'errors': result['errors']
                })
        
        return {
            'stage': stage,
            'total': len(records),
            'passed_count': len(results['passed']),
            'failed_count': len(results['failed']),
            'warning_count': len(results['warnings']),
            'results': results
        }
    
    except Exception as e:
        return {'error': str(e)}


def generate_report(client: gspread.Client, settings: Dict) -> str:
    """Generate a comprehensive validation report."""
    report = []
    report.append("=" * 60)
    report.append("TICKET VALIDATION REPORT")
    report.append("=" * 60)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    
    for stage in ['creation', 'completion', 'export']:
        result = validate_tickets_batch(client, stage, settings)
        
        if 'error' in result:
            report.append(f"\n{stage.upper()}: Error - {result['error']}")
            continue
        
        report.append(f"\n{stage.upper()} STAGE")
        report.append("-" * 40)
        report.append(f"Total tickets: {result['total']}")
        report.append(f"Passed: {result['passed_count']}")
        report.append(f"Failed: {result['failed_count']}")
        report.append(f"Warnings: {result['warning_count']}")
        
        if result['results']['failed']:
            report.append("\nFailed tickets:")
            for fail in result['results']['failed'][:10]:
                report.append(f"  {fail['ticket_number']}:")
                for err in fail['errors']:
                    report.append(f"    - {err['field']}: {err['message']}")
        
        if result['results']['warnings']:
            report.append("\nWarnings:")
            for warn in result['results']['warnings'][:10]:
                report.append(f"  {warn['ticket_number']}:")
                for w in warn['warnings']:
                    report.append(f"    - {w['field']}: {w['message']}")
    
    report.append("\n" + "=" * 60)
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Validate ticket data")
    parser.add_argument("--ticket", help="Specific ticket number to validate")
    parser.add_argument("--stage", choices=['creation', 'completion', 'export'],
                        help="Validation stage")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    creds = get_credentials()
    if not creds:
        print("Error: Could not load Google credentials", file=sys.stderr)
        sys.exit(1)
    
    client = gspread.authorize(creds)
    settings = load_settings(client)
    
    if args.report:
        report = generate_report(client, settings)
        print(report)
    
    elif args.stage:
        result = validate_tickets_batch(client, args.stage, settings)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{args.stage.upper()} VALIDATION")
            print(f"Passed: {result.get('passed_count', 0)}")
            print(f"Failed: {result.get('failed_count', 0)}")
            
            if result.get('results', {}).get('failed'):
                print("\nFailed tickets:")
                for fail in result['results']['failed']:
                    print(f"  {fail['ticket_number']}:")
                    for err in fail['errors']:
                        print(f"    - {err['message']}")
    
    elif args.ticket:
        try:
            spreadsheet = client.open(SPREADSHEET_NAME)
            ticket_data = None
            found_sheet = None
            
            for sheet_name in ['DISPATCH BOARD', 'ACTIVE TICKETS', 'COMPLETED TICKETS']:
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    records = worksheet.get_all_records()
                    
                    for row in records:
                        if str(row.get('ticket_number', row.get('Ticket#', ''))) == args.ticket:
                            ticket_data = row
                            found_sheet = sheet_name
                            break
                    
                    if ticket_data:
                        break
                except:
                    continue
            
            if not ticket_data:
                print(f"Ticket {args.ticket} not found")
                sys.exit(1)
            
            stage_map = {
                'DISPATCH BOARD': 'creation',
                'ACTIVE TICKETS': 'completion',
                'COMPLETED TICKETS': 'export'
            }
            stage = stage_map.get(found_sheet, 'creation')
            
            if stage == 'creation':
                result = validate_creation(ticket_data, settings)
            elif stage == 'completion':
                result = validate_completion(ticket_data)
            else:
                result = validate_export(ticket_data)
            
            result['ticket_number'] = args.ticket
            result['sheet'] = found_sheet
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                status = "✓ VALID" if result['valid'] else "✗ INVALID"
                print(f"\nTicket {args.ticket} ({found_sheet}): {status}")
                
                if result['errors']:
                    print("\nErrors:")
                    for err in result['errors']:
                        print(f"  - {err['field']}: {err['message']}")
                
                if result.get('warnings'):
                    print("\nWarnings:")
                    for warn in result['warnings']:
                        print(f"  - {warn['field']}: {warn['message']}")
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
