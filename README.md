# TicketDrop 2.0 - DOE Workflow

**Rick's Oilfield Hauling Digital Dispatch & Field Ticket System**

A complete replacement for the $5,000+/month AssetWorks system using the DOE (Directive-Orchestration-Execution) agentic framework.

---

## 🎯 Overview

This system follows Nick Saraev's DOE architecture:

| Layer | Purpose | Location |
|-------|---------|----------|
| **Directive** | SOPs and business logic | `directives/` |
| **Orchestration** | AI decision-making | Claude/Agent |
| **Execution** | Deterministic scripts | `execution/` |

**Why this works:** LLMs are probabilistic, business logic is deterministic. This architecture pushes complexity into testable, reliable code.

---

## 📁 Project Structure

```
ticketdrop_doe/
├── CLAUDE.md                    # Agent instructions
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
│
├── directives/                  # SOPs (Markdown)
│   ├── dispatch_workflow.md     # Creating tickets
│   ├── driver_completion.md     # Mobile app workflow
│   ├── axon_export.md          # Billing CSV generation
│   ├── ticket_validation.md    # Data validation rules
│   └── sheets_sync.md          # Google Sheets integration
│
├── execution/                   # Python scripts
│   ├── create_ticket.py        # Ticket creation
│   ├── sync_driver_update.py   # Mobile app sync
│   ├── axon_export.py          # AXON CSV generator
│   └── validate_ticket.py      # Data validation
│
└── .tmp/                        # Temporary files (gitignored)
    └── AXON_Export_*.csv       # Generated exports
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone/download this folder
cd ticketdrop_doe

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Google Sheets Setup

1. Create a new Google Sheet named "Rick's TicketDrop 2.0"
2. Create 5 sheets: DISPATCH BOARD, ACTIVE TICKETS, COMPLETED TICKETS, AXON EXPORT, SETTINGS
3. Set up service account or OAuth credentials
4. Share the spreadsheet with your service account email

### 3. Run Your First Command

```bash
# Validate all tickets
python3 execution/validate_ticket.py --report

# Create a ticket
python3 execution/create_ticket.py \
  --customer "Spur Petroleum Corp" \
  --from-lsd "10-15-052-20W4" \
  --to-lsd "05-22-053-19W4" \
  --product "Crude Oil" \
  --driver "Brant Fandrey" \
  --truck "Unit 1"

# Export to AXON
python3 execution/axon_export.py --export-all
```

---

## 📋 Directives Reference

### dispatch_workflow.md
- **Purpose:** Create and manage field tickets
- **Execution:** `create_ticket.py`
- **Key outputs:** New tickets in DISPATCH BOARD

### driver_completion.md
- **Purpose:** Capture driver field data
- **Execution:** `sync_driver_update.py`
- **Key outputs:** Completed tickets with timestamps, photos, signatures

### axon_export.md
- **Purpose:** Generate billing CSV for AXON import
- **Execution:** `axon_export.py`
- **Key outputs:** B622 format CSV files

### ticket_validation.md
- **Purpose:** Ensure data quality at all stages
- **Execution:** `validate_ticket.py`
- **Key outputs:** Validation reports

### sheets_sync.md
- **Purpose:** Bidirectional sync with mobile app
- **Execution:** Apps Script Web App + sync scripts
- **Key outputs:** Real-time data synchronization

---

## 🔧 Key Commands

### Ticket Management

```bash
# Create single ticket
python3 execution/create_ticket.py --customer "..." --from-lsd "..." ...

# Batch create from CSV
python3 execution/create_ticket.py --batch tickets.csv

# Validate specific ticket
python3 execution/validate_ticket.py --ticket "260101001"
```

### Driver Sync

```bash
# Update field
python3 execution/sync_driver_update.py \
  --ticket "260101001" \
  --field "arrive_load" \
  --value "2026-01-01T08:30:00-07:00"

# Complete ticket
python3 execution/sync_driver_update.py \
  --complete \
  --ticket "260101001" \
  --data '{"actual_volume": 85.5, "hours": 4.25}'
```

### AXON Export

```bash
# Export all unexported
python3 execution/axon_export.py --export-all

# Export date range
python3 execution/axon_export.py --date-from 2026-01-01 --date-to 2026-01-07

# Export for customer
python3 execution/axon_export.py --customer "Spur Petroleum Corp"
```

### Validation

```bash
# Full report
python3 execution/validate_ticket.py --report

# Validate by stage
python3 execution/validate_ticket.py --stage export

# JSON output
python3 execution/validate_ticket.py --ticket "260101001" --json
```

---

## 📊 Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  DISPATCH BOARD │────▶│  ACTIVE TICKETS │────▶│    COMPLETED    │
│    (Create)     │     │   (In Progress) │     │    TICKETS      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   [Dispatch]            [Driver App]            [AXON Export]
```

---

## 🎯 Success Metrics

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Dispatch time | 3+ hrs/day | 15 min/day | 2.75 hrs |
| AR data entry | 5+ hrs/week | 30 min/week | 4.5 hrs |
| Software cost | $5,000+/month | $0/month | $60,000/year |
| Ticket errors | Frequent | Near-zero | Quality |

---

## 🔐 Security Notes

- Service account credentials in `.env` (never commit!)
- OAuth tokens in `token.json` (gitignored)
- Spreadsheet shared only with authorized accounts
- Driver app uses no passwords (controlled access)

---

## 📝 Self-Annealing

When something breaks:
1. **Fix it** - Debug the script
2. **Update the tool** - Modify execution script
3. **Test** - Verify it works
4. **Update directive** - Document the learning
5. **System is stronger** - Knowledge preserved

---

## 📞 Support

**System Owner:** Lily (AR/Office Operations)
**Technical Updates:** Use Claude with `CLAUDE.md` instructions
**Business Owner:** Rick's Oilfield Hauling Management

---

## 📜 License

Internal use only - Rick's Oilfield Hauling Ltd.
