# TicketDrop 2.0 - Agent Instructions

> Rick's Oilfield Hauling Digital Dispatch & Field Ticket System

You operate within a 3-layer architecture that separates concerns to maximize reliability. This system replaces the expensive AssetWorks dispatch software ($5,000+/month) with a custom solution using Google Sheets, Apps Script, and Streamlit.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- SOPs written in Markdown, live in `directives/`
- Define goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions like you'd give dispatch staff

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors
- You're the glue between intent and execution
- Example: You don't manually format AXON CSVs—you read `directives/export_to_axon.md` and run `execution/axon_export.py`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts and Apps Script in `execution/`
- Environment variables stored in `.env`
- Handle API calls, Google Sheets sync, file operations
- Reliable, testable, fast. Use scripts instead of manual work.

**Why this works:** If you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. Push complexity into deterministic code.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again
- Update the directive with what you learned
- Example: AXON CSV import fails → investigate format → discover column order matters → update directive with exact column sequence

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, or common errors—update the directive. These are your instruction set.

## Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Directory structure:**
- `directives/` - SOPs in Markdown (the instruction set)
- `execution/` - Python scripts and Apps Script (deterministic tools)
- `.tmp/` - Intermediate files (CSV exports, temp data)
- `.env` - Environment variables (Google credentials, API keys)
- `credentials.json`, `token.json` - Google OAuth credentials

**Deliverables vs Intermediates:**
- **Deliverables**: Google Sheets, AXON CSV files, completed tickets
- **Intermediates**: Temp exports, sync logs, validation reports

## Rick's Oilfield Hauling Context

**Company:** Rick's Oilfield Hauling Ltd. (Sherwood Park, AB)
**Business:** Petroleum products, water, equipment transport
**Fleet:** 7 trucks, 5 trailers, 11 drivers

**Key Systems:**
- AXON: Accounting/billing software (requires specific CSV format)
- Google Sheets: Dispatch board, ticket tracking
- Streamlit: Mobile driver app

**Pain Points Being Solved:**
1. Dispatch spends 3+ hours/day creating tickets in AssetWorks
2. AR spends 5+ hours/week on manual data entry
3. $5,000+/month software cost
4. Frequent ticket creation errors
5. No real-time driver tracking

**Target Outcomes:**
| Metric | Current | Target |
|--------|---------|--------|
| Dispatch time | 3+ hours/day | 15 min/day |
| AR data entry | 5+ hours/week | 30 min/week |
| Software cost | $5,000+/month | $0/month |
| Ticket errors | Frequent | Near-zero |

## Data Reference

**Drivers (11):**
Brant Fandrey, Dennis Fandrey, Shane Fandrey, Terry Fandrey, Warren Fandrey, Ahmet (Cloud 9), Andcol Oilfield, Derrick Fenton (Smolz), Dwayne Fenton (Smolz), Geoff Fenton (Smolz), Zack Fenton (Smolz)

**Customers (6 main):**
Spur Petroleum Corp, Inter Pipeline Ltd, Canadian Natural Resources, ATCO Pipelines, Pembina Pipeline, Plains Midstream

**Products (7):**
Crude Oil, Condensate, Fresh Water, Produced Water, Slop Oil, Equipment/Tools, Sand/Gravel

**Trucks (7):**
Unit 1, Unit 2, Unit 3, Unit 4, Unit 5, Unit 6, Unit 7

**Ticket Number Format:**
`YYMMDDXXX` - Year/Month/Day + 3-digit daily sequence
Example: `260101001` = First ticket on January 1, 2026

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

