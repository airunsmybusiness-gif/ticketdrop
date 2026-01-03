# Driver Completion Workflow

Capture field data when drivers complete tickets: timestamps, volumes, photos, hazard checks, and signatures.

## Overview

This directive handles the driver-side workflow from receiving an assigned ticket through completion. Drivers use the Streamlit mobile app to capture all required field data.

**Estimated time:** 2-3 minutes per ticket completion
**Offline capable:** Yes - queues locally, syncs when connected

## When to Use

- Driver receives new ticket assignment
- Driver arrives at pickup/delivery locations
- Driver needs to record volumes, photos, timestamps
- Driver completing and signing off on ticket

## Inputs (From Mobile App)

| Parameter | Required | Description |
|-----------|----------|-------------|
| ticket_number | Yes | Ticket being worked |
| driver_id | Yes | Logged-in driver |
| arrive_load | Yes | Timestamp: arrived at pickup |
| depart_load | Yes | Timestamp: departed pickup |
| arrive_offload | Yes | Timestamp: arrived at delivery |
| depart_offload | Yes | Timestamp: departed delivery |
| actual_volume | Yes | Actual m³ loaded |
| photos | Conditional | BOL, scale ticket, meter reading |
| hazard_check | Yes | 10-item safety checklist |
| signature | Yes | Driver digital signature |
| notes | No | Additional field notes |

## Process

### Step 1: Driver Login
Driver selects name from dropdown (no password - field simplicity).
App loads their assigned tickets from ACTIVE TICKETS sheet.

### Step 2: View Assigned Ticket
Driver sees ticket details:
- Customer name
- Pickup location (From LSD)
- Delivery location (To LSD)
- Product type
- Estimated volume
- Special instructions (highlighted if present)
- Priority badge (Hot Shot = red)

### Step 3: Capture Timestamps (4 buttons)
| Button | Records | Auto-fills |
|--------|---------|------------|
| ARRIVE LOAD | arrive_load timestamp | Current GPS time |
| DEPART LOAD | depart_load timestamp | Current GPS time |
| ARRIVE OFFLOAD | arrive_offload timestamp | Current GPS time |
| DEPART OFFLOAD | depart_offload timestamp | Current GPS time |

Timestamps are locked once captured (prevents accidental edits).
System calculates hours worked automatically.

### Step 4: Enter Actual Volume
Driver enters actual m³ loaded.
If significantly different from estimated (±20%), prompt for note.

### Step 5: Capture Photos
| Photo Type | When Required | Purpose |
|------------|---------------|---------|
| BOL (Bill of Lading) | Always | Customer verification |
| Scale Ticket | When available | Volume verification |
| Meter Reading | Liquid loads | Volume verification |
| Secure Ticket | Oversized loads | Transport compliance |

Photos stored with ticket reference in filename.

### Step 6: Complete Hazard Assessment
10-item safety checklist (all must be checked):
1. ☐ PPE worn (hard hat, steel toes, FR clothing)
2. ☐ Vehicle walk-around completed
3. ☐ Load secured properly
4. ☐ Placards displayed correctly
5. ☐ Shipping documents on board
6. ☐ Emergency kit accessible
7. ☐ No leaks or spills observed
8. ☐ Weather conditions assessed
9. ☐ Route hazards identified
10. ☐ Communication device functional

### Step 7: Digital Signature
Driver signs on touchscreen.
Signature captured as PNG, attached to ticket record.

### Step 8: Submit Completion
On submit:
1. Validate all required fields filled
2. Calculate total hours and wait time
3. Sync to Google Sheets (or queue if offline)
4. Move ticket to COMPLETED TICKETS sheet
5. Update status to "COMPLETED"
6. Display confirmation to driver

## Output Schema

### Driver-Captured Fields
```
actual_volume      | m³ (decimal)
arrive_load        | ISO timestamp
depart_load        | ISO timestamp
arrive_offload     | ISO timestamp
depart_offload     | ISO timestamp
hours              | Calculated decimal hours
wait_time          | Calculated waiting time
notes              | Free text
photos_uploaded    | Y/N
photo_bol          | File reference
photo_scale        | File reference
photo_meter        | File reference
photo_secure       | File reference
hazard_check       | Y/N (all 10 items)
signature          | PNG file reference
completed_at       | ISO timestamp
```

### Calculated Fields
```
hours = (depart_offload - arrive_load) in decimal hours
wait_time = (depart_load - arrive_load) + (depart_offload - arrive_offload)
```

## Execution

```bash
# Sync driver update to Google Sheets
python3 execution/sync_driver_update.py \
  --ticket "260101001" \
  --field "arrive_load" \
  --value "2026-01-01T08:30:00-07:00"

# Complete ticket with all data
python3 execution/complete_ticket.py \
  --ticket "260101001" \
  --actual-volume 85.5 \
  --hours 4.25

# Process offline queue
python3 execution/process_offline_queue.py
```

## Error Handling

| Error | Resolution |
|-------|------------|
| "Network unavailable" | Queue locally, show pending count, retry on reconnect |
| "Ticket not found" | Refresh ticket list, contact dispatch |
| "Required field missing" | Highlight field, prevent submission |
| "Photo upload failed" | Retry 3x, then queue for later sync |
| "Signature not captured" | Must complete before submission |

## Offline Mode

When network unavailable:
1. All data stored in browser localStorage
2. "📴 X updates pending sync" shown in footer
3. On reconnect, queue processes automatically
4. Conflicts resolved by timestamp (latest wins)

## Validation Rules

### Required for Completion
- All 4 timestamps ✓
- actual_volume > 0 ✓
- hazard_check = all 10 items ✓
- signature captured ✓

### Logical Checks
- arrive_load < depart_load
- arrive_offload < depart_offload
- depart_load < arrive_offload
- actual_volume within reasonable range (0.1 - 500 m³)

## Files

- `execution/sync_driver_update.py` - Real-time field sync
- `execution/complete_ticket.py` - Ticket completion handler
- `execution/process_offline_queue.py` - Offline queue processor
- `execution/upload_photo.py` - Photo upload to storage

## Learnings

- Drivers often forget to click DEPART LOAD - added reminder after 2 minutes
- Offline mode essential - many rural sites have no cell coverage
- Signature capture works better full-screen on mobile
- Photo compression needed - original files too large for slow connections
- Hazard checklist takes 30 seconds - drivers initially complained, now appreciate
- Timestamp buttons need large tap targets for gloved fingers
- Auto-save on each field prevents data loss

## Mobile App Reference

**Screens:**
1. Login (driver selection dropdown)
2. Ticket List (assigned jobs with status badges)
3. Ticket Detail (work screen)
   - Header: Customer, locations, product
   - 4 timestamp buttons (large, touch-friendly)
   - Volume entry
   - Photo upload (4 slots)
   - Hazard checklist (10 items)
   - Signature pad
   - COMPLETE TICKET button

**Status Badge Colors:**
- Blue: ASSIGNED (waiting for driver)
- Yellow: IN_PROGRESS (driver working)
- Green: COMPLETED (done, synced)
- Orange: PENDING_SYNC (offline queue)
