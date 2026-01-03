# Ticket Validation

Validate ticket data at creation, completion, and export stages.

## Overview

This directive ensures data quality throughout the ticket lifecycle. Validation runs automatically at key checkpoints, catching errors before they cause problems downstream in AXON billing.

## When to Use

- Creating new ticket (dispatch)
- Driver submitting completion
- Before AXON export
- Data quality audits
- Troubleshooting billing issues

## Validation Stages

### Stage 1: Creation Validation
Run when dispatcher clicks CREATE TICKET checkbox.

| Field | Rule | Error Message |
|-------|------|---------------|
| customer | Must exist in SETTINGS.CUSTOMERS | "Unknown customer: {value}" |
| from_lsd | Required, non-empty | "Pickup location required" |
| to_lsd | Required, non-empty | "Delivery location required" |
| product | Must exist in SETTINGS.PRODUCTS | "Unknown product: {value}" |
| driver | Must exist in SETTINGS.DRIVERS | "Unknown driver: {value}" |
| truck | Must exist in SETTINGS.TRUCKS | "Unknown truck: {value}" |
| trailer | If provided, must exist in SETTINGS.TRAILERS | "Unknown trailer: {value}" |

### Stage 2: Completion Validation
Run when driver clicks COMPLETE TICKET button.

| Field | Rule | Error Message |
|-------|------|---------------|
| arrive_load | Required timestamp | "Arrival at pickup time required" |
| depart_load | Required, > arrive_load | "Departure from pickup must be after arrival" |
| arrive_offload | Required, > depart_load | "Arrival at delivery must be after pickup departure" |
| depart_offload | Required, > arrive_offload | "Departure from delivery must be after arrival" |
| actual_volume | Required, > 0 | "Actual volume required (must be > 0)" |
| hazard_check | All 10 items checked | "Complete hazard assessment required" |
| signature | Required PNG | "Driver signature required" |

### Stage 3: Export Validation
Run before generating AXON CSV.

| Field | Rule | Error Message |
|-------|------|---------------|
| status | Must be "COMPLETED" | "Only completed tickets can be exported" |
| actual_volume | Must be > 0 | "Cannot export ticket with zero volume" |
| hours | Must be > 0 | "Cannot export ticket with zero hours" |
| driver | Must match "First Last" format | "Driver name format incorrect" |
| arrive_load | Must be valid timestamp | "Invalid arrival timestamp" |

## LSD Format Validation

Accepts two formats:
1. **Standard LSD:** XX-XX-XXX-XXW5 (e.g., 10-15-052-20W4)
2. **Lease Name:** Any non-empty text (e.g., "Spur Battery North")

```python
import re

def validate_lsd(value):
    if not value or not value.strip():
        return False, "Location required"
    
    # Standard LSD pattern
    lsd_pattern = r'^\d{1,2}-\d{1,2}-\d{1,3}-\d{1,2}W\d$'
    if re.match(lsd_pattern, value.strip()):
        return True, None
    
    # Accept any non-empty string as lease name
    if len(value.strip()) >= 2:
        return True, None
    
    return False, "Invalid location format"
```

## Timestamp Logic Validation

Timestamps must follow logical sequence:

```
arrive_load → depart_load → arrive_offload → depart_offload
     T1     <      T2      <       T3       <       T4
```

```python
def validate_timestamps(arrive_load, depart_load, arrive_offload, depart_offload):
    errors = []
    
    if depart_load <= arrive_load:
        errors.append("Departed pickup before arriving")
    
    if arrive_offload <= depart_load:
        errors.append("Arrived at delivery before leaving pickup")
    
    if depart_offload <= arrive_offload:
        errors.append("Departed delivery before arriving")
    
    # Check for unreasonably long times (potential data entry error)
    total_hours = (depart_offload - arrive_load).total_seconds() / 3600
    if total_hours > 24:
        errors.append(f"Total time exceeds 24 hours ({total_hours:.1f}h)")
    
    return errors
```

## Volume Validation

```python
def validate_volume(actual_volume, est_volume=None):
    errors = []
    warnings = []
    
    if actual_volume <= 0:
        errors.append("Volume must be greater than 0")
    
    if actual_volume > 500:
        warnings.append(f"Volume {actual_volume} m³ seems high - please verify")
    
    if est_volume and abs(actual_volume - est_volume) / est_volume > 0.20:
        diff_pct = abs(actual_volume - est_volume) / est_volume * 100
        warnings.append(f"Actual differs from estimated by {diff_pct:.0f}%")
    
    return errors, warnings
```

## Execution

```bash
# Validate single ticket
python3 execution/validate_ticket.py --ticket "260101001"

# Validate all pending tickets
python3 execution/validate_ticket.py --stage creation

# Validate tickets ready for export
python3 execution/validate_ticket.py --stage export

# Generate validation report
python3 execution/validate_ticket.py --report
```

## Output

### Validation Result Object
```json
{
  "ticket_number": "260101001",
  "stage": "export",
  "valid": false,
  "errors": [
    {"field": "actual_volume", "message": "Volume must be greater than 0"}
  ],
  "warnings": [
    {"field": "hours", "message": "Total time 8.5 hours - verify if correct"}
  ]
}
```

### Validation Report
```
TICKET VALIDATION REPORT
========================
Date: 2026-01-01
Stage: Export

PASSED (12 tickets):
  260101001, 260101002, 260101003...

FAILED (2 tickets):
  260101015 - actual_volume: Volume must be greater than 0
  260101018 - arrive_load: Invalid arrival timestamp

WARNINGS (3 tickets):
  260101005 - hours: Total time 12.3 hours - verify if correct
  260101007 - actual_volume: Actual differs from estimated by 35%
  260101012 - from_lsd: Non-standard LSD format accepted
```

## Error Handling

| Error | Resolution |
|-------|------------|
| "Unknown customer" | Add to SETTINGS.CUSTOMERS or correct spelling |
| "Unknown driver" | Add to SETTINGS.DRIVERS or correct spelling |
| "Invalid timestamp" | Check date/time format, ensure proper entry |
| "Zero volume" | Driver must enter actual volume before completion |
| "Timestamp sequence" | Review and correct timestamp order |

## Files

- `execution/validate_ticket.py` - Main validation script
- `execution/validation_rules.py` - Rule definitions
- `execution/validation_report.py` - Report generator

## Learnings

- Case-insensitive matching helps (Spur vs SPUR)
- Trim whitespace before validation
- Lease names often misspelled - suggest matches
- Timestamps in different timezones cause issues - standardize to MT
- Zero volume usually means driver forgot to enter, not actual zero
- Long ticket times (>12h) often legitimate (standby, multi-stop)
- Driver name format varies (First Last vs Last, First)
