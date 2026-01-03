# AXON CSV Export

Generate billing-ready CSV files in AXON's exact required format (B622).

## Overview

This directive handles exporting completed tickets to CSV format that AXON accounting software can import directly. The format is strict - column order and data formatting must match exactly.

**Critical:** AXON rejects files with incorrect column order or formatting. This directive documents the exact requirements learned through production testing.

## When to Use

- AR needs to bill completed tickets
- End of day/week export for accounting
- Batch export for specific customer or date range
- Re-export after corrections

## Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| date_from | No | Start date filter (YYYY-MM-DD) |
| date_to | No | End date filter (YYYY-MM-DD) |
| customer | No | Filter by customer name |
| export_all | No | Export all unexported tickets |
| ticket_numbers | No | Specific ticket numbers to export |

## AXON B622 Format (19 columns - EXACT ORDER)

| Col | Header | Field | Format | Example |
|-----|--------|-------|--------|---------|
| A | Attachment | attachment | "FALSE" | FALSE |
| B | Customer | customer | Text | Spur Petroleum Corp |
| C | Location | location | "From to To" | 10-15-052-20W4 to 05-22-053-19W4 |
| D | Start Date | start_date | DD-MM-YYYY HH:MM | 01-01-2026 08:30 |
| E | Reference | reference | Text (blank OK) | |
| F | Ticket# | ticket_number | YYMMDDXXX | 260101001 |
| G | Truck# | truck | Unit number | Unit 1 |
| H | Operator | operator | "Last, First" | Fandrey, Brant |
| I | Trailer# | trailer | Trailer ID | T-001 |
| J | Product | product | Product name | Crude Oil |
| K | Actual Vol | actual_volume | Decimal m³ | 85.50 |
| L | Product2 | product2 | Text (blank OK) | |
| M | From LSD | from_lsd | LSD format | 10-15-052-20W4 |
| N | To LSD | to_lsd | LSD format | 05-22-053-19W4 |
| O | Hours | hours | Decimal hours | 4.25 |
| P | Charge | charge | Currency (AR fills) | |
| Q | Job Desc | job_desc | Auto-generated | Crude Oil - Spur Petroleum Corp |
| R | Company | company | Fixed | Rick's Oilfield Hauling |
| S | Status | status | Fixed | Completed |

## Process

### Step 1: Query Completed Tickets
Read from COMPLETED TICKETS sheet where:
- `status` = "COMPLETED"
- `exported` = "N" (or blank)
- Matches date/customer filters if provided

### Step 2: Transform Data
For each ticket, transform to AXON format:

```python
# Operator name format: "Last, First"
name_parts = driver.split()
operator = f"{name_parts[-1]}, {name_parts[0]}"

# Location format: "From to To"
location = f"{from_lsd} to {to_lsd}"

# Start date format: DD-MM-YYYY HH:MM
start_date = arrive_load.strftime("%d-%m-%Y %H:%M")

# Job description: "{Product} - {Customer}"
job_desc = f"{product} - {customer}"

# Fixed values
attachment = "FALSE"
company = "Rick's Oilfield Hauling"
status = "Completed"
```

### Step 3: Validate Data
Before export, verify:
- All required fields populated
- actual_volume > 0
- hours > 0
- Date format correct
- No special characters that break CSV

### Step 4: Generate CSV
Write to CSV with exact column order (A-S).
Use UTF-8 encoding, comma delimiter, double-quote text fields.

Filename format: `AXON_Export_YYYYMMDD_HHMMSS.csv`

### Step 5: Mark as Exported
Update COMPLETED TICKETS sheet:
- Set `exported` = "Y"
- Set `exported_at` = current timestamp
- Set `export_file` = generated filename

### Step 6: Deliver File
Save to `C:\AxonETAAttach\` (Windows AXON import folder)
Or provide download link from Google Sheet.

## Execution

```bash
# Export all unexported tickets
python3 execution/axon_export.py --export-all

# Export specific date range
python3 execution/axon_export.py \
  --date-from "2026-01-01" \
  --date-to "2026-01-07"

# Export for specific customer
python3 execution/axon_export.py --customer "Spur Petroleum Corp"

# Export specific tickets
python3 execution/axon_export.py --tickets "260101001,260101002,260101003"

# Re-export (ignores exported flag)
python3 execution/axon_export.py --tickets "260101001" --force
```

## Output

CSV file saved to:
- Local: `.tmp/AXON_Export_YYYYMMDD_HHMMSS.csv`
- Windows: `C:\AxonETAAttach\` (for AXON import)
- Download link displayed in terminal

## Error Handling

| Error | Resolution |
|-------|------------|
| "No tickets to export" | Check date range, or all already exported |
| "Missing required field" | List tickets with missing data, skip or fix |
| "Invalid volume" | Volume must be > 0, check ticket |
| "Invalid hours" | Hours must be > 0, recalculate from timestamps |
| "AXON import failed" | Check column order, date format, encoding |

## Validation Rules

### Required for Export
- ticket_number ✓
- customer ✓
- from_lsd ✓
- to_lsd ✓
- product ✓
- driver ✓
- truck ✓
- actual_volume > 0 ✓
- hours > 0 ✓
- arrive_load timestamp ✓

### Data Cleaning
- Strip leading/trailing whitespace
- Replace line breaks with spaces
- Escape double quotes in text
- Round volumes to 2 decimal places
- Round hours to 2 decimal places

## Files

- `execution/axon_export.py` - Main export script
- `execution/validate_for_export.py` - Pre-export validation
- `execution/mark_exported.py` - Update export status

## Learnings

- Column order is CRITICAL - AXON rejects if wrong
- Date format must be DD-MM-YYYY (not MM-DD-YYYY)
- Operator name must be "Last, First" format
- Empty fields should be blank, not "N/A" or "null"
- UTF-8 BOM causes issues - use plain UTF-8
- Volumes over 999 need no comma separator
- Hours can have decimal (4.25 not 4:15)
- AXON folder path varies by installation
- Re-export requires --force flag to prevent duplicates
- Batch exports work better than individual tickets

## AXON Import Path

Default Windows path: `C:\AxonETAAttach\`
(Confirm with AR team for Rick's specific installation)

## Sample CSV Output

```csv
Attachment,Customer,Location,Start Date,Reference,Ticket#,Truck#,Operator,Trailer#,Product,Actual Vol,Product2,From LSD,To LSD,Hours,Charge,Job Desc,Company,Status
FALSE,Spur Petroleum Corp,10-15-052-20W4 to 05-22-053-19W4,01-01-2026 08:30,,260101001,Unit 1,"Fandrey, Brant",T-001,Crude Oil,85.50,,10-15-052-20W4,05-22-053-19W4,4.25,,"Crude Oil - Spur Petroleum Corp",Rick's Oilfield Hauling,Completed
```
