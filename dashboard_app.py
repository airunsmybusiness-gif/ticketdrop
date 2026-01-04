#!/usr/bin/env python3
"""
TicketDrop 2.0 - Dashboard (AssetWorks Style)
Exact replica of AssetWorks UI with table view and filters.

Run with: streamlit run dashboard_app.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Page config - WIDE layout like AssetWorks
st.set_page_config(
    page_title="TicketDrop 2.0",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# AssetWorks-style CSS
st.markdown("""
<style>
    /* Dark header bar */
    .main-header {
        background: #2C3E50;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    
    /* Filter row styling */
    .filter-row {
        background: #F8F9FA;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    
    /* Table styling */
    .ticket-table {
        font-size: 12px;
        width: 100%;
    }
    
    .ticket-row {
        background: #FFFFFF;
        border-bottom: 1px solid #DEE2E6;
        padding: 8px;
    }
    
    .ticket-row:nth-child(even) {
        background: #F8F9FA;
    }
    
    .ticket-row:hover {
        background: #E3F2FD;
    }
    
    /* Status buttons */
    .status-btn {
        padding: 5px 15px;
        border-radius: 3px;
        margin: 2px;
        cursor: pointer;
        border: 1px solid #ccc;
    }
    
    .status-active {
        background: #4CAF50;
        color: white;
    }
    
    /* Column headers */
    .col-header {
        background: #34495E;
        color: white;
        padding: 8px;
        font-weight: bold;
        font-size: 11px;
    }
    
    /* Sidebar icons */
    .sidebar-icon {
        padding: 10px;
        text-align: center;
        cursor: pointer;
    }
    
    .stApp { background-color: #ECEFF1; }
    
    /* Make inputs smaller */
    .stSelectbox > div > div { font-size: 12px; }
    .stTextInput > div > div > input { font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# Google Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_client():
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    return gspread.authorize(creds)

def load_all_tickets():
    """Load tickets from all sheets."""
    client = get_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    
    all_tickets = []
    
    # Active tickets
    try:
        active = spreadsheet.worksheet('ACTIVE TICKETS')
        for t in active.get_all_records():
            t['TICKET STATE'] = t.get('STATUS', 'NEW')
            if t['TICKET STATE'] == 'ASSIGNED':
                t['TICKET STATE'] = 'NEW'
            all_tickets.append(t)
    except Exception as e:
        pass
    
    # Completed tickets
    try:
        completed = spreadsheet.worksheet('COMPLETED TICKETS')
        for t in completed.get_all_records():
            t['TICKET STATE'] = 'COMPLETED'
            all_tickets.append(t)
    except:
        pass
    
    return all_tickets

def load_settings():
    """Load settings for filters."""
    client = get_client()
    sheet = client.open("Rick's TicketDrop 2.0").worksheet('SETTINGS')
    data = sheet.get_all_values()
    
    drivers, customers, products, trucks, trailers = [], [], [], [], []
    if data:
        for row in data[1:]:
            if len(row) > 0 and row[0]: drivers.append(row[0])
            if len(row) > 1 and row[1]: customers.append(row[1])
            if len(row) > 2 and row[2]: products.append(row[2])
            if len(row) > 3 and row[3]: trucks.append(row[3])
            if len(row) > 4 and row[4]: trailers.append(row[4])
    
    return drivers, customers, products, trucks, trailers

# ============================================================
# HEADER BAR (Like AssetWorks)
# ============================================================

col_logo, col_title, col_spacer, col_filters = st.columns([1, 2, 4, 5])

with col_logo:
    st.markdown("### 🛢️")

with col_title:
    st.markdown("## TicketDrop 2.0")

with col_filters:
    # Date range filters (like AssetWorks top bar)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown("**TICKET FILTERS**")
    with c2:
        start_date = st.date_input("From", value=datetime.now() - timedelta(days=7), label_visibility="collapsed")
    with c3:
        start_time = st.time_input("", value=datetime.strptime("00:00", "%H:%M").time(), label_visibility="collapsed")
    with c4:
        end_date = st.date_input("To", value=datetime.now(), label_visibility="collapsed")
    with c5:
        end_time = st.time_input(" ", value=datetime.strptime("23:59", "%H:%M").time(), label_visibility="collapsed")
    with c6:
        load_btn = st.button("🔄 Load", type="primary")

st.markdown("---")

# ============================================================
# SIDEBAR ICONS (Like AssetWorks left sidebar)
# ============================================================

# Create sidebar-style layout
col_sidebar, col_main = st.columns([1, 20])

with col_sidebar:
    st.markdown("🗺️")  # Map
    st.markdown("📋")  # Tickets
    st.markdown("📊")  # Reports
    st.markdown("⚙️")  # Settings

# ============================================================
# MAIN CONTENT
# ============================================================

with col_main:
    # Load data
    if load_btn:
        st.cache_data.clear()
    
    try:
        all_tickets = load_all_tickets()
        drivers, customers, products, trucks, trailers = load_settings()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    # ============================================================
    # TICKET STATE BUTTONS (Like AssetWorks)
    # ============================================================
    
    st.markdown("##### Ticket State")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # Count by state
    new_count = len([t for t in all_tickets if t.get('TICKET STATE') == 'NEW'])
    active_count = len([t for t in all_tickets if t.get('TICKET STATE') == 'IN_PROGRESS'])
    completed_count = len([t for t in all_tickets if t.get('TICKET STATE') == 'COMPLETED'])
    
    with col1:
        show_all = st.button(f"📋 All ({len(all_tickets)})", use_container_width=True)
    with col2:
        show_new = st.button(f"🔵 New/Active ({new_count})", use_container_width=True)
    with col3:
        show_active = st.button(f"🟡 In Progress ({active_count})", use_container_width=True)
    with col4:
        show_completed = st.button(f"🟢 Completed ({completed_count})", use_container_width=True)
    with col5:
        show_unassigned = st.button("⚪ Unassigned", use_container_width=True)
    with col6:
        show_selected = st.button("☑️ Selected", use_container_width=True)
    
    # Determine filter state
    if 'state_filter' not in st.session_state:
        st.session_state.state_filter = 'All'
    
    if show_all:
        st.session_state.state_filter = 'All'
    elif show_new:
        st.session_state.state_filter = 'NEW'
    elif show_active:
        st.session_state.state_filter = 'IN_PROGRESS'
    elif show_completed:
        st.session_state.state_filter = 'COMPLETED'
    
    st.markdown("---")
    
    # ============================================================
    # COLUMN FILTER ROW (Like AssetWorks)
    # ============================================================
    
    # Column headers with filter inputs
    cols = st.columns([1, 2, 3, 2, 2, 2, 1, 2, 1, 2, 1, 1])
    
    with cols[0]:
        st.markdown("**☑️**")
    with cols[1]:
        st.markdown("**Customer Name**")
        filter_customer = st.selectbox("cust", ['Filter'] + list(set(customers)), label_visibility="collapsed", key="f_cust")
    with cols[2]:
        st.markdown("**Location**")
        filter_location = st.text_input("loc", placeholder="Filter", label_visibility="collapsed", key="f_loc")
    with cols[3]:
        st.markdown("**Start Date**")
        st.markdown("*↑ Sort*")
    with cols[4]:
        st.markdown("**Reference #**")
        filter_ref = st.text_input("ref", placeholder="Filter", label_visibility="collapsed", key="f_ref")
    with cols[5]:
        st.markdown("**Customer Ticket**")
        filter_cust_ticket = st.text_input("ct", placeholder="Filter", label_visibility="collapsed", key="f_ct")
    with cols[6]:
        st.markdown("**Truck #**")
        filter_truck = st.selectbox("truck", ['Filter'] + list(set(trucks)), label_visibility="collapsed", key="f_truck")
    with cols[7]:
        st.markdown("**Trailer #**")
        filter_trailer = st.selectbox("trailer", ['Filter'] + list(set(trailers)), label_visibility="collapsed", key="f_trail")
    with cols[8]:
        st.markdown("**Operator**")
        filter_driver = st.selectbox("driver", ['Filter'] + list(set(drivers)), label_visibility="collapsed", key="f_drv")
    with cols[9]:
        st.markdown("**Product**")
        filter_product = st.selectbox("prod", ['Filter'] + list(set(products)), label_visibility="collapsed", key="f_prod")
    with cols[10]:
        st.markdown("**Volume**")
    with cols[11]:
        st.markdown("**Hours**")
    
    st.markdown("---")
    
    # ============================================================
    # APPLY FILTERS
    # ============================================================
    
    filtered = []
    for t in all_tickets:
        # State filter
        if st.session_state.state_filter != 'All':
            if t.get('TICKET STATE') != st.session_state.state_filter:
                continue
        
        # Customer filter
        if filter_customer != 'Filter' and t.get('CUSTOMER') != filter_customer:
            continue
        
        # Location filter
        if filter_location:
            loc_str = f"{t.get('FROM LSD', '')} {t.get('TO LSD', '')}".lower()
            if filter_location.lower() not in loc_str:
                continue
        
        # Truck filter
        if filter_truck != 'Filter' and t.get('TRUCK') != filter_truck:
            continue
        
        # Trailer filter
        if filter_trailer != 'Filter' and t.get('TRAILER') != filter_trailer:
            continue
        
        # Driver filter
        if filter_driver != 'Filter' and t.get('DRIVER') != filter_driver:
            continue
        
        # Product filter
        if filter_product != 'Filter' and t.get('PRODUCT') != filter_product:
            continue
        
        # Reference filter
        if filter_ref and filter_ref not in str(t.get('TICKET #', '')):
            continue
        
        filtered.append(t)
    
    # ============================================================
    # TICKET TABLE (Like AssetWorks)
    # ============================================================
    
    st.markdown(f"**Showing {len(filtered)}/{len(all_tickets)}**")
    
    # Table header
    header_cols = st.columns([1, 2, 3, 2, 2, 2, 1, 1, 2, 1, 1, 1])
    headers = ["☑️", "Customer", "Location", "Start Date", "Ref #", "Cust Ticket", "Truck", "Trailer", "Operator", "Product", "Vol", "Hrs"]
    
    for i, h in enumerate(headers):
        with header_cols[i]:
            st.markdown(f"**{h}**")
    
    # Table rows
    for idx, t in enumerate(filtered[:100]):  # Limit to 100 rows
        row_cols = st.columns([1, 2, 3, 2, 2, 2, 1, 1, 2, 1, 1, 1])
        
        # Checkbox
        with row_cols[0]:
            st.checkbox("", key=f"chk_{idx}", label_visibility="collapsed")
        
        # Customer
        with row_cols[1]:
            st.markdown(f"<small>{t.get('CUSTOMER', '')[:20]}</small>", unsafe_allow_html=True)
        
        # Location
        with row_cols[2]:
            from_loc = t.get('FROM LSD', '')[:15]
            to_loc = t.get('TO LSD', '')[:15]
            st.markdown(f"<small>{from_loc} To {to_loc}</small>", unsafe_allow_html=True)
        
        # Start Date
        with row_cols[3]:
            date_str = t.get('DATE', '') or t.get('ARRIVE LOAD', '')
            st.markdown(f"<small>{str(date_str)[:16]}</small>", unsafe_allow_html=True)
        
        # Reference #
        with row_cols[4]:
            st.markdown(f"<small>{t.get('TICKET #', '')}</small>", unsafe_allow_html=True)
        
        # Customer Ticket
        with row_cols[5]:
            cust_ticket = t.get('CUSTOMER TICKET', '') or t.get('CONSIGNOR LOAD', '')
            st.markdown(f"<small>{cust_ticket}</small>", unsafe_allow_html=True)
        
        # Truck
        with row_cols[6]:
            st.markdown(f"<small>{t.get('TRUCK', '')}</small>", unsafe_allow_html=True)
        
        # Trailer
        with row_cols[7]:
            st.markdown(f"<small>{t.get('TRAILER', '')}</small>", unsafe_allow_html=True)
        
        # Operator
        with row_cols[8]:
            driver = t.get('DRIVER', '')
            # Format as "Last, First" if possible
            parts = driver.split()
            if len(parts) >= 2:
                driver_formatted = f"{parts[-1]}, {parts[0]}"
            else:
                driver_formatted = driver
            st.markdown(f"<small>{driver_formatted}</small>", unsafe_allow_html=True)
        
        # Product
        with row_cols[9]:
            st.markdown(f"<small>{t.get('PRODUCT', '')[:10]}</small>", unsafe_allow_html=True)
        
        # Volume
        with row_cols[10]:
            vol = t.get('ACTUAL VOLUME', '') or t.get('EST VOLUME', '')
            st.markdown(f"<small>{vol}</small>", unsafe_allow_html=True)
        
        # Hours
        with row_cols[11]:
            hrs = t.get('HOURS', '')
            st.markdown(f"<small>{hrs}</small>", unsafe_allow_html=True)
    
    if len(filtered) > 100:
        st.warning(f"Showing first 100 of {len(filtered)} tickets. Use filters to narrow down.")
    
    # ============================================================
    # BOTTOM STATUS BAR (Like AssetWorks)
    # ============================================================
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"**Showing {len(filtered)}/{len(all_tickets)}**")
    
    with col2:
        total_vol = sum(float(t.get('ACTUAL VOLUME') or t.get('EST VOLUME') or 0) for t in filtered if t.get('ACTUAL VOLUME') or t.get('EST VOLUME'))
        st.markdown(f"**Total Volume: {total_vol:,.1f} m³**")
    
    with col3:
        total_hrs = sum(float(t.get('HOURS') or 0) for t in filtered if t.get('HOURS'))
        st.markdown(f"**Total Hours: {total_hrs:,.1f}**")
    
    with col4:
        exported = len([t for t in filtered if str(t.get('EXPORTED', '')).upper() == 'Y'])
        st.markdown(f"**Exported: {exported}/{len(filtered)}**")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center;color:#888;font-size:11px;'>TicketDrop 2.0 | Rick's Oilfield Hauling | 4606 - 51 Ave, Redwater AB T0A 2W0</p>", unsafe_allow_html=True)
