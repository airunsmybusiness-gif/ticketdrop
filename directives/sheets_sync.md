# Google Sheets Sync

Synchronize data between Google Sheets (backend) and the mobile driver app.

## Overview

Google Sheets serves as the central database for TicketDrop. This directive handles bidirectional sync: pushing tickets to drivers and receiving completion data back.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│   DISPATCH BOARD    │────▶│    ACTIVE TICKETS    │────▶│ COMPLETED TICKETS  │
│  (Ticket Creation)  │     │  (Driver Working)    │     │   (AR Billing)     │
└─────────────────────┘     └──────────────────────┘     └────────────────────┘
                                      │  ▲
                                      │  │
                                      ▼  │
                            ┌──────────────────────┐
                            │   MOBILE DRIVER APP  │
                            │   (Streamlit PWA)    │
                            └──────────────────────┘
```

## When to Use

- Mobile app needs to fetch assigned tickets
- Driver updates need to sync to Google Sheets
- Offline queue needs to process
- AR dashboard needs real-time data

## API Endpoints (Apps Script Web App)

### GET /tickets?driver={name}
Returns tickets assigned to driver.

**Request:**
```
GET https://script.google.com/.../exec?action=getTickets&driver=Brant%20Fandrey
```

**Response:**
```json
{
  "status": "success",
  "tickets": [
    {
      "ticket_number": "260101001",
      "date": "2026-01-01",
      "customer": "Spur Petroleum Corp",
      "from_lsd": "10-15-052-20W4",
      "to_lsd": "05-22-053-19W4",
      "product": "Crude Oil",
      "truck": "Unit 1",
      "est_volume": 100,
      "status": "ASSIGNED"
    }
  ]
}
```

### POST /update
Update ticket field from driver app.

**Request:**
```json
{
  "action": "updateTicket",
  "ticket_number": "260101001",
  "updates": {
    "arrive_load": "2026-01-01T08:30:00-07:00",
    "status": "IN_PROGRESS"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "ticket_number": "260101001",
  "updated_fields": ["arrive_load", "status"]
}
```

### POST /complete
Mark ticket as completed with all driver data.

**Request:**
```json
{
  "action": "completeTicket",
  "ticket_number": "260101001",
  "data": {
    "arrive_load": "2026-01-01T08:30:00-07:00",
    "depart_load": "2026-01-01T09:15:00-07:00",
    "arrive_offload": "2026-01-01T10:45:00-07:00",
    "depart_offload": "2026-01-01T11:00:00-07:00",
    "actual_volume": 85.5,
    "hazard_check": true,
    "signature": true,
    "notes": "Good load, no issues"
  }
}
```

## Process

### Dispatch → Driver Sync

1. Dispatcher creates ticket in DISPATCH BOARD
2. Checks CREATE TICKET checkbox
3. Apps Script `onEdit` trigger fires
4. Ticket validated and moved to ACTIVE TICKETS
5. Driver app polls every 30 seconds
6. New ticket appears in driver's list

### Driver → Sheets Sync

1. Driver captures timestamp/data in app
2. App sends POST to Web App endpoint
3. Apps Script updates ACTIVE TICKETS row
4. On completion, ticket moves to COMPLETED TICKETS
5. If offline, updates queue locally

### Offline Queue Processing

1. Updates stored in browser localStorage
2. Queue displays pending count in footer
3. On reconnect, queue processes FIFO
4. Conflicts resolved by timestamp (latest wins)
5. Failed syncs retry 3x with exponential backoff

## Execution

```bash
# Read tickets for a driver
python3 execution/read_sheet.py \
  --sheet "Rick's TicketDrop 2.0" \
  --tab "ACTIVE TICKETS" \
  --filter "driver=Brant Fandrey"

# Update a ticket field
python3 execution/update_sheet.py \
  --sheet "Rick's TicketDrop 2.0" \
  --tab "ACTIVE TICKETS" \
  --ticket "260101001" \
  --field "arrive_load" \
  --value "2026-01-01T08:30:00-07:00"

# Move ticket between sheets
python3 execution/move_ticket.py \
  --ticket "260101001" \
  --from "ACTIVE TICKETS" \
  --to "COMPLETED TICKETS"
```

## Google Sheets Structure

### DISPATCH BOARD
| Column | Field | Purpose |
|--------|-------|---------|
| A | Create | Checkbox trigger |
| B | Ticket# | Auto-generated |
| C | Date | Job date |
| D | Customer | Customer name |
| E | From LSD | Pickup location |
| F | To LSD | Delivery location |
| G | Product | Load type |
| H | Driver | Assigned driver |
| I | Truck | Unit number |
| J | Trailer | Trailer ID |
| K | Est Vol | Estimated m³ |
| L | Instructions | Special notes |
| M | Priority | Normal/Hot Shot |

### ACTIVE TICKETS
Same as DISPATCH BOARD plus:
| Column | Field | Purpose |
|--------|-------|---------|
| N | Status | ASSIGNED/IN_PROGRESS |
| O | Arrive Load | Driver timestamp |
| P | Depart Load | Driver timestamp |
| Q | Arrive Offload | Driver timestamp |
| R | Depart Offload | Driver timestamp |
| S | Actual Vol | Driver-entered |
| T | Hours | Calculated |
| U | Wait Time | Calculated |
| V | Hazard Check | Y/N |
| W | Signature | Y/N |
| X | Notes | Driver notes |
| Y | Created At | Timestamp |
| Z | Updated At | Timestamp |

### COMPLETED TICKETS
Same as ACTIVE TICKETS plus:
| Column | Field | Purpose |
|--------|-------|---------|
| AA | Completed At | Timestamp |
| AB | Exported | Y/N |
| AC | Exported At | Timestamp |
| AD | Export File | Filename |

### SETTINGS
| Column | List | Items |
|--------|------|-------|
| A | DRIVERS | 11 names |
| B | CUSTOMERS | 6+ names |
| C | PRODUCTS | 7 types |
| D | TRUCKS | 7 units |
| E | TRAILERS | 5 IDs |

## Error Handling

| Error | Resolution |
|-------|------------|
| "Spreadsheet not found" | Check sheet name, verify access |
| "Permission denied" | Share sheet with service account |
| "Ticket not found" | Refresh driver app, check ticket exists |
| "Rate limit exceeded" | Implement backoff, batch updates |
| "Network timeout" | Queue for retry, show offline status |

## Files

- `execution/read_sheet.py` - Read data from sheets
- `execution/update_sheet.py` - Update single field
- `execution/move_ticket.py` - Transfer between sheets
- `execution/append_to_sheet.py` - Add new rows
- `Code.gs` - Apps Script (deployed as Web App)

## Learnings

- Apps Script Web App has 6-minute timeout - keep requests small
- Rate limit: 100 requests/100 seconds per user
- Batch updates more efficient than individual calls
- Poll interval 30s balances responsiveness vs API limits
- Use exponential backoff for retries (1s, 2s, 4s, 8s)
- Cache driver's tickets locally to reduce API calls
- Timestamps must include timezone (-07:00 for Alberta)
- Empty cells return "" not null in Apps Script
- Row numbers change when tickets move - use ticket_number as key

## Apps Script Web App Deployment

1. Open Google Sheet → Extensions → Apps Script
2. Paste Code.gs content
3. Deploy → New deployment
4. Type: Web app
5. Execute as: Me
6. Who has access: Anyone (or specific users)
7. Deploy and copy URL

URL format: `https://script.google.com/macros/s/{DEPLOYMENT_ID}/exec`
