# Dispatch Workflow

Create and manage field tickets from initial job request through driver assignment.

## Overview

This directive handles the complete dispatch workflow: receiving job requests, creating tickets in Google Sheets, assigning drivers, and syncing to the mobile app.

**Estimated time:** 30 seconds per ticket (down from 5+ minutes)
**Tested at:** Rick's Oilfield Hauling, 30+ tickets/day

## When to Use

- Customer calls/emails with a load request
- Dispatcher needs to create a new field ticket
- Assigning or reassigning a driver to a job
- Updating ticket details before driver starts

## Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| customer | Yes | Customer name from approved list |
| from_lsd | Yes | Pickup location (LSD or lease name) |
| to_lsd | Yes | Delivery location (LSD or lease name) |
| product | Yes | Load type (Crude Oil, Fresh Water, etc.) |
| driver | Yes | Assigned driver name |
| truck | Yes | Truck unit number |
| trailer | No | Trailer ID (if applicable) |
| est_volume | No | Estimated volume in m³ |
| special_instructions | No | Hot shot, standby, wait time notes |
| priority | No | Normal, Hot Shot, Emergency |

## Process

### Step 1: Validate Inputs
Before creating a ticket, verify:
- Customer exists in SETTINGS sheet
- Driver is available (not already on active ticket)
- Truck is available
- Product type is valid
- LSD format is correct (XX-XX-XXX-XXW5 or lease name)

If validation fails, return specific error message.

### Step 2: Generate Ticket Number
Format: `YYMMDDXXX`
- YY = 2-digit year
- MM = 2-digit month
- DD = 2-digit day
- XXX = 3-digit sequence (001, 002, etc.)

Run `execution/generate_ticket_number.py` to get next available number.

### Step 3: Create Ticket in DISPATCH BOARD
Insert new row in DISPATCH BOARD sheet with:
- Column A: Empty checkbox (unchecked)
- Column B: Generated ticket number
- Column C: Today's date
- Column D-onwards: All ticket fields

### Step 4: Move to ACTIVE TICKETS
When dispatcher checks the CREATE TICKET checkbox:
1. Validate all required fields are filled
2. Copy row to ACTIVE TICKETS sheet
3. Set status to "ASSIGNED"
4. Clear row from DISPATCH BOARD
5. Send notification to driver app (via API sync)

### Step 5: Update Driver App
The mobile app polls for new tickets every 30 seconds.
Driver sees new ticket in their list with status badge.

## Output Schema

### Ticket Record (23 fields)
```
ticket_number       | YYMMDDXXX format
date               | YYYY-MM-DD
customer           | Company name
from_lsd           | Pickup location
to_lsd             | Delivery location
product            | Load type
driver             | Driver name
truck              | Unit number
trailer            | Trailer ID
est_volume         | Estimated m³
special_instructions| Notes
priority           | Normal/Hot Shot/Emergency
status             | PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
created_at         | ISO timestamp
created_by         | Dispatcher name
```

## Execution

```bash
# Create a single ticket
python3 execution/create_ticket.py \
  --customer "Spur Petroleum Corp" \
  --from-lsd "10-15-052-20W4" \
  --to-lsd "05-22-053-19W4" \
  --product "Crude Oil" \
  --driver "Brant Fandrey" \
  --truck "Unit 1"

# Batch create from CSV
python3 execution/create_ticket.py --batch tickets.csv

# Check driver availability
python3 execution/check_availability.py --driver "Brant Fandrey"
```

## Error Handling

| Error | Resolution |
|-------|------------|
| "Invalid customer" | Check SETTINGS sheet, add if new customer |
| "Driver unavailable" | Check ACTIVE TICKETS for driver's current job |
| "Duplicate ticket" | Ticket # already exists, system auto-increments |
| "Missing required field" | Return list of missing fields |
| "Invalid LSD format" | Accept lease names or XX-XX-XXX-XXW5 format |

## Validation Rules

### Required Fields
- customer ✓
- from_lsd ✓
- to_lsd ✓
- product ✓
- driver ✓
- truck ✓

### Optional Fields
- trailer
- est_volume
- special_instructions
- priority (defaults to "Normal")

## Files

- `execution/create_ticket.py` - Ticket creation script
- `execution/generate_ticket_number.py` - Ticket number generator
- `execution/check_availability.py` - Driver/truck availability checker
- `execution/validate_ticket.py` - Input validation

## Learnings

- LSD format validation was initially too strict - now accepts lease names too
- Drivers prefer seeing pickup location prominently in notifications
- "Hot Shot" priority tickets should push to top of driver's list
- Truck availability check must account for multi-day jobs
- Sequence numbers reset daily at midnight (Mountain Time)

## Google Sheet Reference

**Spreadsheet:** Rick's TicketDrop 2.0
**DISPATCH BOARD columns:**
A=Create, B=Ticket#, C=Date, D=Customer, E=From LSD, F=To LSD, G=Product, H=Driver, I=Truck, J=Trailer, K=Est Vol, L=Instructions, M=Priority

**SETTINGS sheet lists:**
- Column A: DRIVERS
- Column B: CUSTOMERS
- Column C: PRODUCTS
- Column D: TRUCKS
- Column E: TRAILERS
