#!/usr/bin/env python3
"""
TicketDrop 2.0 - Driver Mobile App (FIXED VERSION)
Run with: streamlit run driver_app.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Page config
st.set_page_config(
    page_title="TicketDrop - Driver",
    page_icon="🚛",
    layout="centered"
)

# Light theme CSS
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .stButton > button { width: 100%; height: 60px; font-size: 18px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# Google Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_client():
    creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    return gspread.authorize(creds)

def load_drivers():
    client = get_client()
    sheet = client.open("Rick's TicketDrop 2.0").worksheet('SETTINGS')
    data = sheet.get_all_values()
    return [row[0] for row in data[1:] if row and row[0]]

def get_tickets(driver_name):
    client = get_client()
    sheet = client.open("Rick's TicketDrop 2.0").worksheet('ACTIVE TICKETS')
    records = sheet.get_all_records()
    return [t for t in records if t.get('DRIVER') == driver_name and t.get('STATUS') != 'COMPLETED']

def update_cell(ticket_num, field, value):
    """Update a single cell in ACTIVE TICKETS."""
    client = get_client()
    sheet = client.open("Rick's TicketDrop 2.0").worksheet('ACTIVE TICKETS')
    data = sheet.get_all_values()
    headers = data[0]
    
    # Find row
    row_num = None
    for i, row in enumerate(data[1:], start=2):
        if row[0] == ticket_num:
            row_num = i
            break
    
    if not row_num:
        return False, "Ticket not found"
    
    # Find column
    if field not in headers:
        return False, f"Column '{field}' not found in headers: {headers}"
    
    col_num = headers.index(field) + 1
    
    # Update
    sheet.update_cell(row_num, col_num, value)
    return True, "Updated"

def get_fresh_ticket(ticket_num):
    """Get fresh ticket data from Google Sheet."""
    client = get_client()
    sheet = client.open("Rick's TicketDrop 2.0").worksheet('ACTIVE TICKETS')
    records = sheet.get_all_records()
    for t in records:
        if str(t.get('TICKET #')) == str(ticket_num):
            return t
    return None

def complete_ticket(ticket_num, form_data):
    """Move ticket to COMPLETED TICKETS."""
    client = get_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    
    active = spreadsheet.worksheet('ACTIVE TICKETS')
    data = active.get_all_values()
    headers = data[0]
    
    # Find ticket
    row_num = None
    row_data = None
    for i, row in enumerate(data[1:], start=2):
        if row[0] == ticket_num:
            row_num = i
            row_data = row
            break
    
    if not row_num:
        return False
    
    # Create dict
    ticket_dict = dict(zip(headers, row_data))
    ticket_dict['STATUS'] = 'COMPLETED'
    ticket_dict['COMPLETED AT'] = datetime.now().isoformat()
    ticket_dict.update(form_data)
    
    # Add to COMPLETED
    completed = spreadsheet.worksheet('COMPLETED TICKETS')
    completed_headers = completed.row_values(1)
    new_row = [ticket_dict.get(h, '') for h in completed_headers]
    completed.append_row(new_row)
    
    # Delete from ACTIVE
    active.delete_rows(row_num)
    return True

# ============================================================
# SESSION STATE
# ============================================================
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'ticket_num' not in st.session_state:
    st.session_state.ticket_num = None

# ============================================================
# LOGIN PAGE
# ============================================================
if not st.session_state.driver:
    st.markdown("# 🚛 TicketDrop 2.0")
    st.markdown("### Rick's Oilfield Hauling - Driver App")
    st.markdown("---")
    
    drivers = load_drivers()
    driver = st.selectbox("👷 Select Your Name", [''] + drivers)
    
    if st.button("🔓 LOG IN", type="primary"):
        if driver:
            st.session_state.driver = driver
            st.rerun()
        else:
            st.error("Select your name")

# ============================================================
# TICKET LIST PAGE
# ============================================================
elif not st.session_state.ticket_num:
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown(f"### 👷 {st.session_state.driver}")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.driver = None
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Tickets"):
        st.rerun()
    
    tickets = get_tickets(st.session_state.driver)
    
    if not tickets:
        st.info("📭 No tickets assigned to you.")
    else:
        st.markdown(f"### 📋 Your Tickets ({len(tickets)})")
        
        for ticket in tickets:
            ticket_num = ticket.get('TICKET #', '')
            customer = ticket.get('CUSTOMER', '')
            from_loc = ticket.get('FROM LSD', '')
            to_loc = ticket.get('TO LSD', '')
            product = ticket.get('PRODUCT', '')
            priority = ticket.get('PRIORITY', 'Normal')
            
            st.markdown(f"""
**{ticket_num}** {'🔴 HOT' if priority != 'Normal' else ''}  
🏢 {customer}  
📍 {from_loc} → {to_loc}  
🛢️ {product}
            """)
            
            if st.button(f"📂 Open Ticket {ticket_num}", key=f"open_{ticket_num}"):
                st.session_state.ticket_num = str(ticket_num)
                st.rerun()
            
            st.markdown("---")

# ============================================================
# TICKET DETAIL PAGE
# ============================================================
else:
    ticket_num = st.session_state.ticket_num
    
    # Back button
    if st.button("← Back to Tickets"):
        st.session_state.ticket_num = None
        st.rerun()
    
    # Get FRESH ticket data
    ticket = get_fresh_ticket(ticket_num)
    
    if not ticket:
        st.error("Ticket not found!")
        st.session_state.ticket_num = None
        st.rerun()
    
    # Header
    st.markdown(f"# 🎫 Ticket {ticket_num}")
    st.markdown(f"""
**Customer:** {ticket.get('CUSTOMER', '')}  
**From:** {ticket.get('FROM LSD', '')}  
**To:** {ticket.get('TO LSD', '')}  
**Product:** {ticket.get('PRODUCT', '')}  
**Est. Volume:** {ticket.get('EST VOLUME', '')} m³
    """)
    
    if ticket.get('SPECIAL INSTRUCTIONS'):
        st.warning(f"📋 **Instructions:** {ticket.get('SPECIAL INSTRUCTIONS')}")
    
    # ============================================================
    # TIMESTAMPS SECTION
    # ============================================================
    st.markdown("---")
    st.markdown("## ⏱️ Timestamps")
    
    col1, col2 = st.columns(2)
    
    # ARRIVE LOAD
    with col1:
        arrive_load = ticket.get('ARRIVE LOAD', '')
        if arrive_load:
            st.success(f"✅ Arrived Load: {str(arrive_load)[:16]}")
        else:
            if st.button("📍 ARRIVE AT LOAD", key="btn_arrive_load", type="primary"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success, msg = update_cell(ticket_num, 'ARRIVE LOAD', timestamp)
                if success:
                    update_cell(ticket_num, 'STATUS', 'IN_PROGRESS')
                    st.success("✅ Timestamp saved!")
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")
    
    # DEPART LOAD
    with col2:
        depart_load = ticket.get('DEPART LOAD', '')
        if depart_load:
            st.success(f"✅ Departed Load: {str(depart_load)[:16]}")
        else:
            if st.button("🚛 DEPART LOAD", key="btn_depart_load"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success, msg = update_cell(ticket_num, 'DEPART LOAD', timestamp)
                if success:
                    st.success("✅ Timestamp saved!")
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")
    
    col3, col4 = st.columns(2)
    
    # ARRIVE OFFLOAD
    with col3:
        arrive_offload = ticket.get('ARRIVE OFFLOAD', '')
        if arrive_offload:
            st.success(f"✅ Arrived Offload: {str(arrive_offload)[:16]}")
        else:
            if st.button("📍 ARRIVE AT OFFLOAD", key="btn_arrive_offload"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success, msg = update_cell(ticket_num, 'ARRIVE OFFLOAD', timestamp)
                if success:
                    st.success("✅ Timestamp saved!")
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")
    
    # DEPART OFFLOAD
    with col4:
        depart_offload = ticket.get('DEPART OFFLOAD', '')
        if depart_offload:
            st.success(f"✅ Departed Offload: {str(depart_offload)[:16]}")
        else:
            if st.button("🏁 DEPART OFFLOAD", key="btn_depart_offload"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success, msg = update_cell(ticket_num, 'DEPART OFFLOAD', timestamp)
                if success:
                    st.success("✅ Timestamp saved!")
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")
    
    # ============================================================
    # COMPLETION FORM
    # ============================================================
    st.markdown("---")
    st.markdown("## ✅ Complete Ticket")
    
    with st.form("complete_form"):
        
        # Volume & Hours
        st.markdown("### 📊 Volume & Hours")
        col1, col2 = st.columns(2)
        with col1:
            actual_volume = st.number_input("Actual Volume (m³)", min_value=0.0, value=float(ticket.get('EST VOLUME') or 0), step=0.5)
        with col2:
            hours = st.number_input("Hours Charged", min_value=0.0, value=0.0, step=0.5)
        
        # Job Description
        job_desc = st.text_area("Job Description", placeholder="e.g., Haul town H2O from shop to frac")
        
        # CONSIGNOR AT LOAD
        st.markdown("---")
        st.markdown("### 👤 Consignor at LOAD Site")
        consignor_load = st.text_input("Consignor Name (person at pickup)", placeholder="Name of person at load site")
        consignor_load_confirm = st.checkbox("Consignor confirmed loading ✓")
        
        # CONSIGNOR AT OFFLOAD
        st.markdown("---")
        st.markdown("### 👤 Consignor at OFFLOAD Site")
        consignor_offload = st.text_input("Consignor Name (person at delivery)", placeholder="Name of person at offload site")
        consignor_offload_confirm = st.checkbox("Consignor confirmed offloading ✓")
        
        # Placards
        st.markdown("---")
        st.markdown("### 🏷️ Transporting Placards")
        col1, col2 = st.columns(2)
        with col1:
            p1 = st.checkbox("UN 2924 Mixed Waste Water")
            p2 = st.checkbox("UN 1267 Petroleum Crude Oil")
            p3 = st.checkbox("UN 1268 Condensate")
        with col2:
            p4 = st.checkbox("Produced Water")
            p5 = st.checkbox("Brine Water")
            p6 = st.checkbox("Fresh Water")
        
        # Hazard Assessment
        st.markdown("---")
        st.markdown("### ⚠️ Site Hazard Assessment")
        col1, col2, col3 = st.columns(3)
        with col1:
            h1 = st.checkbox("Access")
            h2 = st.checkbox("Weather")
            h3 = st.checkbox("Wind Direction")
        with col2:
            h4 = st.checkbox("Slip / Trip")
            h5 = st.checkbox("Working Alone")
            h6 = st.checkbox("Powerline")
        with col3:
            h7 = st.checkbox("PPE Used")
            h8 = st.checkbox("Fire Extinguisher")
            h9 = st.checkbox("Communication")
        
        # Notes
        st.markdown("---")
        notes = st.text_area("📝 Notes", placeholder="Any issues or comments...")
        
        # Driver Signature
        st.markdown("---")
        st.markdown("### ✍️ Driver Signature")
        signature = st.checkbox(f"I, **{st.session_state.driver}**, confirm this ticket is complete and accurate")
        
        # Submit
        submitted = st.form_submit_button("🚀 COMPLETE TICKET", type="primary")
        
        if submitted:
            errors = []
            if actual_volume <= 0:
                errors.append("Enter actual volume")
            if not signature:
                errors.append("Driver signature required")
            if not ticket.get('ARRIVE LOAD'):
                errors.append("Missing: Arrive Load timestamp")
            if not ticket.get('DEPART LOAD'):
                errors.append("Missing: Depart Load timestamp")
            if not ticket.get('ARRIVE OFFLOAD'):
                errors.append("Missing: Arrive Offload timestamp")
            if not ticket.get('DEPART OFFLOAD'):
                errors.append("Missing: Depart Offload timestamp")
            
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                # Collect placards
                placards = []
                if p1: placards.append("UN 2924")
                if p2: placards.append("UN 1267")
                if p3: placards.append("UN 1268")
                if p4: placards.append("Produced Water")
                if p5: placards.append("Brine Water")
                if p6: placards.append("Fresh Water")
                
                # Calculate hours if not entered
                if hours == 0:
                    try:
                        arr = datetime.strptime(str(ticket.get('ARRIVE LOAD'))[:19], "%Y-%m-%d %H:%M:%S")
                        dep = datetime.strptime(str(ticket.get('DEPART OFFLOAD'))[:19], "%Y-%m-%d %H:%M:%S")
                        hours = round((dep - arr).total_seconds() / 3600, 2)
                    except:
                        hours = 0
                
                form_data = {
                    'ACTUAL VOLUME': actual_volume,
                    'HOURS': hours,
                    'JOB DESCRIPTION': job_desc,
                    'CONSIGNOR LOAD': consignor_load,
                    'CONSIGNOR OFFLOAD': consignor_offload,
                    'PLACARDS': ', '.join(placards),
                    'HAZARD CHECK': 'Y',
                    'SIGNATURE': 'Y',
                    'NOTES': notes
                }
                
                if complete_ticket(ticket_num, form_data):
                    st.success("🎉 Ticket completed!")
                    st.balloons()
                    st.session_state.ticket_num = None
                    st.rerun()
                else:
                    st.error("Error completing ticket")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center;color:#888;'>TicketDrop 2.0 | Rick's Oilfield Hauling</p>", unsafe_allow_html=True)
