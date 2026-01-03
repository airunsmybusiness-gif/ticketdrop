#!/usr/bin/env python3
"""
TicketDrop 2.0 - MASTER FIX SCRIPT
Fixes all Google Sheet headers and ensures everything works.

Run with: python3 fix_everything.py
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

print("\n" + "="*60)
print("🔧 TicketDrop 2.0 - MASTER FIX SCRIPT")
print("="*60)

# Connect
print("\n📡 Connecting to Google Sheets...")
creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open("Rick's TicketDrop 2.0")
print("✓ Connected!")

# ============================================================
# FIX 1: DISPATCH BOARD Headers
# ============================================================
print("\n--- Fixing DISPATCH BOARD ---")
dispatch = spreadsheet.worksheet('DISPATCH BOARD')

dispatch_headers = [
    'CREATE', 'TICKET #', 'DATE', 'CUSTOMER', 'FROM LSD', 'TO LSD', 
    'PRODUCT', 'DRIVER', 'TRUCK', 'TRAILER', 'EST VOLUME', 
    'SPECIAL INSTRUCTIONS', 'PRIORITY'
]

dispatch.update('A1:M1', [dispatch_headers])
print(f"✓ DISPATCH BOARD: {len(dispatch_headers)} columns set")

# ============================================================
# FIX 2: ACTIVE TICKETS Headers (THIS IS THE IMPORTANT ONE!)
# ============================================================
print("\n--- Fixing ACTIVE TICKETS ---")
active = spreadsheet.worksheet('ACTIVE TICKETS')

active_headers = [
    'TICKET #',           # A
    'DATE',               # B
    'CUSTOMER',           # C
    'FROM LSD',           # D
    'TO LSD',             # E
    'PRODUCT',            # F
    'DRIVER',             # G
    'TRUCK',              # H
    'TRAILER',            # I
    'EST VOLUME',         # J
    'SPECIAL INSTRUCTIONS', # K
    'PRIORITY',           # L
    'STATUS',             # M
    'ARRIVE LOAD',        # N  <-- TIMESTAMP
    'DEPART LOAD',        # O  <-- TIMESTAMP
    'ARRIVE OFFLOAD',     # P  <-- TIMESTAMP
    'DEPART OFFLOAD',     # Q  <-- TIMESTAMP
    'ACTUAL VOLUME',      # R
    'HOURS',              # S
    'WAIT TIME',          # T
    'JOB DESCRIPTION',    # U
    'CONSIGNOR LOAD',     # V
    'CONSIGNOR OFFLOAD',  # W
    'PLACARDS',           # X
    'RESIDUE',            # Y
    'HAZARD CHECK',       # Z
    'SIGNATURE',          # AA
    'NOTES',              # AB
    'CREATED AT',         # AC
    'UPDATED AT'          # AD
]

active.update('A1:AD1', [active_headers])
print(f"✓ ACTIVE TICKETS: {len(active_headers)} columns set")
print("  ✓ ARRIVE LOAD column: N")
print("  ✓ DEPART LOAD column: O")
print("  ✓ ARRIVE OFFLOAD column: P")
print("  ✓ DEPART OFFLOAD column: Q")

# ============================================================
# FIX 3: COMPLETED TICKETS Headers
# ============================================================
print("\n--- Fixing COMPLETED TICKETS ---")
completed = spreadsheet.worksheet('COMPLETED TICKETS')

completed_headers = active_headers + [
    'COMPLETED AT',       # AE
    'EXPORTED',           # AF
    'EXPORTED AT',        # AG
    'EXPORT FILE'         # AH
]

completed.update('A1:AH1', [completed_headers])
print(f"✓ COMPLETED TICKETS: {len(completed_headers)} columns set")

# ============================================================
# FIX 4: AXON EXPORT Headers
# ============================================================
print("\n--- Fixing AXON EXPORT ---")
axon = spreadsheet.worksheet('AXON EXPORT')

axon_headers = [
    'Attachment', 'Customer', 'Location', 'Start Date', 'Reference',
    'Ticket#', 'Truck#', 'Operator', 'Trailer#', 'Product',
    'Actual Vol', 'Product2', 'From LSD', 'To LSD', 'Hours',
    'Charge', 'Job Desc', 'Company', 'Status'
]

axon.update('A1:S1', [axon_headers])
print(f"✓ AXON EXPORT: {len(axon_headers)} columns set")

# ============================================================
# FIX 5: SETTINGS (make sure it has data)
# ============================================================
print("\n--- Checking SETTINGS ---")
settings = spreadsheet.worksheet('SETTINGS')
data = settings.get_all_values()

if len(data) <= 1:
    print("  Adding sample data to SETTINGS...")
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
    ]
    settings.update('A1:E9', settings_data)
    print("✓ SETTINGS: Sample data added")
else:
    print(f"✓ SETTINGS: Already has {len(data)} rows")

# ============================================================
# DONE!
# ============================================================
print("\n" + "="*60)
print("🎉 ALL FIXES COMPLETE!")
print("="*60)
print("""
Your Google Sheet is now properly configured.

NEXT STEPS:
1. Create a NEW ticket from Dispatch App
2. Open Driver App and log in
3. Open the ticket
4. The timestamp buttons should now work!

To run the apps:
  python3 -m streamlit run dispatch_app.py
  python3 -m streamlit run driver_app.py
  python3 -m streamlit run ar_export_app.py
""")
