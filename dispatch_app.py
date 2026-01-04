#!/usr/bin/env python3
"""
TicketDrop 2.0 - Dispatch Interface
A simple web form for dispatch to create and send tickets to drivers.

Run with: streamlit run dispatch_app.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="TicketDrop 2.0 - Dispatch",
    page_icon="🛢️",
    layout="wide"
)

# Google Auth
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_google_client():
    """Connect to Google Sheets."""
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES) if hasattr(st, "secrets") and "gcp_service_account" in st.secrets else Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_settings():
    """Load dropdown options from SETTINGS tab."""
    client = get_google_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    settings = spreadsheet.worksheet('SETTINGS')
    data = settings.get_all_values()
    
    if not data:
        return {}, {}, {}, {}, {}
    
    headers = data[0]
    columns = {h: [] for h in headers}
    
    for row in data[1:]:
        for i, val in enumerate(row):
            if val and i < len(headers):
                columns[headers[i]].append(val)
    
    return (
        columns.get('DRIVERS', []),
        columns.get('CUSTOMERS', []),
        columns.get('PRODUCTS', []),
        columns.get('TRUCKS', []),
        columns.get('TRAILERS', [])
    )

def generate_ticket_number(client):
    """Generate next ticket number (YYMMDDXXX format)."""
    today = datetime.now()
    prefix = today.strftime("%y%m%d")
    
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    existing = []
    
    for sheet_name in ['DISPATCH BOARD', 'ACTIVE TICKETS', 'COMPLETED TICKETS']:
        try:
            ws = spreadsheet.worksheet(sheet_name)
            records = ws.get_all_values()
            for row in records[1:]:  # Skip header
                if row and row[0].startswith(prefix):
                    existing.append(row[0])
                elif row and len(row) > 1 and row[1].startswith(prefix):
                    existing.append(row[1])
        except:
            continue
    
    if not existing:
        return f"{prefix}001"
    
    sequences = []
    for num in existing:
        try:
            sequences.append(int(num[-3:]))
        except:
            continue
    
    next_seq = max(sequences) + 1 if sequences else 1
    return f"{prefix}{next_seq:03d}"

def create_ticket(ticket_data):
    """Create a new ticket in DISPATCH BOARD."""
    client = get_google_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    
    # Generate ticket number
    ticket_number = generate_ticket_number(client)
    
    # Add to DISPATCH BOARD
    dispatch = spreadsheet.worksheet('DISPATCH BOARD')
    
    row = [
        '',  # CREATE checkbox
        ticket_number,
        datetime.now().strftime("%Y-%m-%d"),
        ticket_data['customer'],
        ticket_data['from_lsd'],
        ticket_data['to_lsd'],
        ticket_data['product'],
        ticket_data['driver'],
        ticket_data['truck'],
        ticket_data.get('trailer', ''),
        ticket_data.get('est_volume', ''),
        ticket_data.get('instructions', ''),
        ticket_data.get('priority', 'Normal')
    ]
    
    dispatch.append_row(row)
    
    # Also add to ACTIVE TICKETS so driver can see it
    active = spreadsheet.worksheet('ACTIVE TICKETS')
    active_row = [
        ticket_number,
        datetime.now().strftime("%Y-%m-%d"),
        ticket_data['customer'],
        ticket_data['from_lsd'],
        ticket_data['to_lsd'],
        ticket_data['product'],
        ticket_data['driver'],
        ticket_data['truck'],
        ticket_data.get('trailer', ''),
        ticket_data.get('est_volume', ''),
        ticket_data.get('instructions', ''),
        ticket_data.get('priority', 'Normal'),
        'ASSIGNED',  # STATUS
        '', '', '', '',  # Timestamps
        '', '', '',  # Volume, hours, wait
        '', '',  # Hazard, signature
        '',  # Notes
        datetime.now().isoformat(),  # Created at
        ''  # Updated at
    ]
    active.append_row(active_row)
    
    return ticket_number

def get_active_tickets():
    """Get list of active tickets."""
    client = get_google_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    active = spreadsheet.worksheet('ACTIVE TICKETS')
    records = active.get_all_records()
    return records

# ============================================================
# MAIN APP
# ============================================================

def main():
    # Header
    st.markdown("""
    <h1 style='text-align: center;'>🛢️ TicketDrop 2.0</h1>
    <h3 style='text-align: center; color: gray;'>Rick's Oilfield Hauling - Dispatch</h3>
    <hr>
    """, unsafe_allow_html=True)
    
    # Load settings
    try:
        drivers, customers, products, trucks, trailers = load_settings()
    except Exception as e:
        st.error(f"❌ Could not connect to Google Sheets: {e}")
        st.stop()
    
    # Two columns
    col1, col2 = st.columns([1, 1])
    
    # ============================================================
    # LEFT COLUMN: Create Ticket Form
    # ============================================================
    with col1:
        st.markdown("### 📝 Create New Ticket")
        
        with st.form("create_ticket_form"):
            # Customer
            customer = st.selectbox("🏢 Customer *", options=[''] + customers, index=0)
            
            # Locations
            loc_col1, loc_col2 = st.columns(2)
            with loc_col1:
                from_lsd = st.text_input("📍 From (Pickup) *", placeholder="10-15-052-20W4")
            with loc_col2:
                to_lsd = st.text_input("📍 To (Delivery) *", placeholder="05-22-053-19W4")
            
            # Product
            product = st.selectbox("🛢️ Product *", options=[''] + products, index=0)
            
            # Driver & Truck
            driver_col, truck_col = st.columns(2)
            with driver_col:
                driver = st.selectbox("👷 Driver *", options=[''] + drivers, index=0)
            with truck_col:
                truck = st.selectbox("🚛 Truck *", options=[''] + trucks, index=0)
            
            # Trailer & Volume
            trailer_col, vol_col = st.columns(2)
            with trailer_col:
                trailer = st.selectbox("🚚 Trailer", options=[''] + trailers, index=0)
            with vol_col:
                est_volume = st.text_input("📊 Est. Volume (m³)", placeholder="100")
            
            # Priority
            priority = st.selectbox("⚡ Priority", options=['Normal', 'Hot Shot', 'Emergency'], index=0)
            
            # Instructions
            instructions = st.text_area("📋 Special Instructions", placeholder="Any notes for the driver...")
            
            # Submit button
            submitted = st.form_submit_button("🚀 CREATE & SEND TICKET", use_container_width=True, type="primary")
            
            if submitted:
                # Validate required fields
                errors = []
                if not customer:
                    errors.append("Customer is required")
                if not from_lsd:
                    errors.append("Pickup location is required")
                if not to_lsd:
                    errors.append("Delivery location is required")
                if not product:
                    errors.append("Product is required")
                if not driver:
                    errors.append("Driver is required")
                if not truck:
                    errors.append("Truck is required")
                
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    # Create the ticket
                    try:
                        ticket_data = {
                            'customer': customer,
                            'from_lsd': from_lsd,
                            'to_lsd': to_lsd,
                            'product': product,
                            'driver': driver,
                            'truck': truck,
                            'trailer': trailer,
                            'est_volume': est_volume,
                            'priority': priority,
                            'instructions': instructions
                        }
                        
                        ticket_number = create_ticket(ticket_data)
                        
                        st.success(f"✅ Ticket **{ticket_number}** created and sent to **{driver}**!")
                        st.balloons()
                        
                        # Clear cache to refresh active tickets
                        st.cache_data.clear()
                        
                    except Exception as e:
                        st.error(f"❌ Error creating ticket: {e}")
    
    # ============================================================
    # RIGHT COLUMN: Active Tickets
    # ============================================================
    with col2:
        st.markdown("### 📋 Active Tickets")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        try:
            tickets = get_active_tickets()
            
            if not tickets:
                st.info("No active tickets. Create one! 👈")
            else:
                for ticket in tickets:
                    ticket_num = ticket.get('TICKET #', 'Unknown')
                    customer = ticket.get('CUSTOMER', '')
                    driver = ticket.get('DRIVER', '')
                    status = ticket.get('STATUS', 'ASSIGNED')
                    from_loc = ticket.get('FROM LSD', '')
                    to_loc = ticket.get('TO LSD', '')
                    product = ticket.get('PRODUCT', '')
                    priority = ticket.get('PRIORITY', 'Normal')
                    
                    # Status color
                    if status == 'ASSIGNED':
                        status_color = '🔵'
                    elif status == 'IN_PROGRESS':
                        status_color = '🟡'
                    elif status == 'COMPLETED':
                        status_color = '🟢'
                    else:
                        status_color = '⚪'
                    
                    # Priority badge
                    if priority == 'Hot Shot':
                        priority_badge = '🔴 HOT SHOT'
                    elif priority == 'Emergency':
                        priority_badge = '🚨 EMERGENCY'
                    else:
                        priority_badge = ''
                    
                    with st.container():
                        st.markdown(f"""
                        <div style='background: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {"#ff4444" if priority != "Normal" else "#4CAF50"};'>
                            <div style='display: flex; justify-content: space-between;'>
                                <strong style='font-size: 18px;'>{ticket_num}</strong>
                                <span>{status_color} {status} {priority_badge}</span>
                            </div>
                            <div style='color: #888; margin-top: 5px;'>
                                🏢 {customer}<br>
                                👷 {driver}<br>
                                📍 {from_loc} → {to_loc}<br>
                                🛢️ {product}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error loading tickets: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>TicketDrop 2.0 | Rick's Oilfield Hauling</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
