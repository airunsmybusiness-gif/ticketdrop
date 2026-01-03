#!/usr/bin/env python3
"""
One-Time Setup: Creates all tabs and populates SETTINGS in Google Sheet
Run this once to set up your Rick's TicketDrop 2.0 spreadsheet.
"""

import gspread
from google.oauth2.service_account import Credentials

# Google Auth
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

print("\n" + "="*60)
print("TicketDrop 2.0 - One-Time Sheet Setup")
print("="*60 + "\n")

# Connect
creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open("Rick's TicketDrop 2.0")
print(f"✓ Connected to: {spreadsheet.title}")

# Define the tabs we need
TABS_NEEDED = ['DISPATCH BOARD', 'ACTIVE TICKETS', 'COMPLETED TICKETS', 'AXON EXPORT', 'SETTINGS']

# Get existing tabs
existing_tabs = [ws.title for ws in spreadsheet.worksheets()]
print(f"  Existing tabs: {existing_tabs}")

# Create missing tabs
for tab_name in TABS_NEEDED:
    if tab_name not in existing_tabs:
        spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
        print(f"✓ Created tab: {tab_name}")
    else:
        print(f"  Tab exists: {tab_name}")

# Delete default Sheet1 if it exists and we have other tabs
existing_tabs = [ws.title for ws in spreadsheet.worksheets()]
if 'Sheet1' in existing_tabs and len(existing_tabs) > 1:
    spreadsheet.del_worksheet(spreadsheet.worksheet('Sheet1'))
    print(f"✓ Deleted: Sheet1")

# Set up DISPATCH BOARD headers
print("\n--- Setting up DISPATCH BOARD ---")
dispatch_board = spreadsheet.worksheet('DISPATCH BOARD')
dispatch_headers = [
    'CREATE', 'TICKET #', 'DATE', 'CUSTOMER', 'FROM LSD', 'TO LSD', 
    'PRODUCT', 'DRIVER', 'TRUCK', 'TRAILER', 'EST VOLUME', 
    'SPECIAL INSTRUCTIONS', 'PRIORITY'
]
dispatch_board.update('A1:M1', [dispatch_headers])
print(f"✓ Added headers to DISPATCH BOARD")

# Set up ACTIVE TICKETS headers
print("\n--- Setting up ACTIVE TICKETS ---")
active_tickets = spreadsheet.worksheet('ACTIVE TICKETS')
active_headers = [
    'TICKET #', 'DATE', 'CUSTOMER', 'FROM LSD', 'TO LSD', 
    'PRODUCT', 'DRIVER', 'TRUCK', 'TRAILER', 'EST VOLUME',
    'SPECIAL INSTRUCTIONS', 'PRIORITY', 'STATUS',
    'ARRIVE LOAD', 'DEPART LOAD', 'ARRIVE OFFLOAD', 'DEPART OFFLOAD',
    'ACTUAL VOLUME', 'HOURS', 'WAIT TIME', 'HAZARD CHECK', 'SIGNATURE',
    'NOTES', 'CREATED AT', 'UPDATED AT'
]
active_tickets.update('A1:Y1', [active_headers])
print(f"✓ Added headers to ACTIVE TICKETS")

# Set up COMPLETED TICKETS headers
print("\n--- Setting up COMPLETED TICKETS ---")
completed_tickets = spreadsheet.worksheet('COMPLETED TICKETS')
completed_headers = active_headers + ['COMPLETED AT', 'EXPORTED', 'EXPORTED AT', 'EXPORT FILE']
completed_tickets.update('A1:AC1', [completed_headers])
print(f"✓ Added headers to COMPLETED TICKETS")

# Set up AXON EXPORT headers (B622 format)
print("\n--- Setting up AXON EXPORT ---")
axon_export = spreadsheet.worksheet('AXON EXPORT')
axon_headers = [
    'Attachment', 'Customer', 'Location', 'Start Date', 'Reference',
    'Ticket#', 'Truck#', 'Operator', 'Trailer#', 'Product',
    'Actual Vol', 'Product2', 'From LSD', 'To LSD', 'Hours',
    'Charge', 'Job Desc', 'Company', 'Status'
]
axon_export.update('A1:S1', [axon_headers])
print(f"✓ Added headers to AXON EXPORT")

# Set up SETTINGS with Rick's data
print("\n--- Setting up SETTINGS ---")
settings = spreadsheet.worksheet('SETTINGS')

settings_data = [
    ['DRIVERS', 'CUSTOMERS', 'PRODUCTS', 'TRUCKS', 'TRAILERS'],
    ['Brant Fandrey', 'Spur Petroleum Corp', 'Crude Oil', 'Unit 1', 'T-001'],
    ['Dennis Fandrey', 'Inter Pipeline Ltd', 'Fresh Water', 'Unit 2', 'T-002'],
    ['Shane Fandrey', 'Canadian Natural Resources', 'Produced Water', 'Unit 3', 'T-003'],
    ['Terry Fandrey', 'ATCO Pipelines', 'Condensate', 'Unit 4', 'T-004'],
    ['Warren Fandrey', 'Pembina Pipeline', 'Slop Oil', 'Unit 5', 'T-005'],
    ['Ahmet (Cloud 9)', 'Plains Midstream', 'Equipment/Tools', 'Unit 6', ''],
    ['Andcol Oilfield', '', 'Sand/Gravel', 'Unit 7', ''],
    ['Derrick Fenton (Smolz)', '', '', '', ''],
    ['Dwayne Fenton (Smolz)', '', '', '', ''],
    ['Geoff Fenton (Smolz)', '', '', '', ''],
    ['Zack Fenton (Smolz)', '', '', '', ''],
]

settings.update('A1:E12', settings_data)
print(f"✓ Added SETTINGS data (11 drivers, 6 customers, 7 products, 7 trucks, 5 trailers)")

# Done!
print("\n" + "="*60)
print("🎉 SETUP COMPLETE!")
print("="*60)
print(f"\nYour spreadsheet is ready: {spreadsheet.url}")
print("\nTabs created:")
for tab in TABS_NEEDED:
    print(f"  ✓ {tab}")
print("\nNext step: Try creating a ticket!")
print("  python3 execution/create_ticket.py --customer \"Spur Petroleum Corp\" --from-lsd \"10-15-052-20W4\" --to-lsd \"05-22-053-19W4\" --product \"Crude Oil\" --driver \"Brant Fandrey\" --truck \"Unit 1\"")
print("")
