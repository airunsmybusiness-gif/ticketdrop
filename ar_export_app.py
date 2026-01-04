#!/usr/bin/env python3
"""
TicketDrop 2.0 - AR Export App
One-click export of completed tickets to AXON CSV format.

Run with: streamlit run ar_export_app.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import io

# Page config
st.set_page_config(
    page_title="TicketDrop - AR Export",
    page_icon="📊",
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
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    return gspread.authorize(creds)

def get_completed_tickets():
    """Get all completed tickets."""
    client = get_google_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    completed = spreadsheet.worksheet('COMPLETED TICKETS')
    records = completed.get_all_records()
    return records

def mark_as_exported(ticket_numbers):
    """Mark tickets as exported."""
    client = get_google_client()
    spreadsheet = client.open("Rick's TicketDrop 2.0")
    completed = spreadsheet.worksheet('COMPLETED TICKETS')
    
    data = completed.get_all_values()
    headers = data[0]
    
    # Find column indices
    ticket_col = headers.index('TICKET #') if 'TICKET #' in headers else 0
    exported_col = headers.index('EXPORTED') if 'EXPORTED' in headers else None
    exported_at_col = headers.index('EXPORTED AT') if 'EXPORTED AT' in headers else None
    
    if exported_col is None:
        return
    
    for i, row in enumerate(data[1:], start=2):
        if row[ticket_col] in ticket_numbers:
            completed.update_cell(i, exported_col + 1, 'Y')
            if exported_at_col:
                completed.update_cell(i, exported_at_col + 1, datetime.now().isoformat())

def format_operator_name(driver_name):
    """Convert 'First Last' to 'Last, First' for AXON."""
    parts = driver_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {parts[0]}"
    return driver_name

def format_date_for_axon(iso_timestamp):
    """Convert ISO timestamp to DD-MM-YYYY HH:MM format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%d-%m-%Y %H:%M")
    except:
        return iso_timestamp

def generate_axon_csv(tickets):
    """Generate AXON B622 format CSV."""
    rows = []
    
    for ticket in tickets:
        row = {
            'Attachment': 'FALSE',
            'Customer': ticket.get('CUSTOMER', ''),
            'Location': f"{ticket.get('FROM LSD', '')} to {ticket.get('TO LSD', '')}",
            'Start Date': format_date_for_axon(ticket.get('ARRIVE LOAD', '')),
            'Reference': '',
            'Ticket#': ticket.get('TICKET #', ''),
            'Truck#': ticket.get('TRUCK', ''),
            'Operator': format_operator_name(ticket.get('DRIVER', '')),
            'Trailer#': ticket.get('TRAILER', ''),
            'Product': ticket.get('PRODUCT', ''),
            'Actual Vol': ticket.get('ACTUAL VOLUME', ''),
            'Product2': '',
            'From LSD': ticket.get('FROM LSD', ''),
            'To LSD': ticket.get('TO LSD', ''),
            'Hours': ticket.get('HOURS', ''),
            'Charge': '',
            'Job Desc': f"{ticket.get('PRODUCT', '')} - {ticket.get('CUSTOMER', '')}",
            'Company': "Rick's Oilfield Hauling",
            'Status': 'Completed'
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

# ============================================================
# MAIN APP
# ============================================================
def main():
    st.markdown("""
    <h1 style='text-align: center;'>📊 TicketDrop 2.0</h1>
    <h3 style='text-align: center; color: gray;'>AR Export - AXON Billing</h3>
    <hr>
    """, unsafe_allow_html=True)
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Get completed tickets
    try:
        all_tickets = get_completed_tickets()
    except Exception as e:
        st.error(f"❌ Error connecting to Google Sheets: {e}")
        st.stop()
    
    if not all_tickets:
        st.info("📭 No completed tickets yet.")
        st.stop()
    
    # Split into exported and not exported
    unexported = [t for t in all_tickets if t.get('EXPORTED', '').upper() != 'Y']
    exported = [t for t in all_tickets if t.get('EXPORTED', '').upper() == 'Y']
    
    # ============================================================
    # TABS
    # ============================================================
    tab1, tab2, tab3 = st.tabs(["📤 Ready to Export", "✅ Already Exported", "📋 All Tickets"])
    
    # ============================================================
    # TAB 1: Ready to Export
    # ============================================================
    with tab1:
        st.markdown(f"### 📤 Tickets Ready for Export ({len(unexported)})")
        
        if not unexported:
            st.success("✅ All tickets have been exported!")
        else:
            # Show tickets
            df_display = pd.DataFrame(unexported)
            display_cols = ['TICKET #', 'DATE', 'CUSTOMER', 'DRIVER', 'PRODUCT', 'ACTUAL VOLUME', 'HOURS']
            available_cols = [c for c in display_cols if c in df_display.columns]
            
            st.dataframe(df_display[available_cols], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Export button
            st.markdown("### 🚀 Export to AXON")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate CSV
                axon_df = generate_axon_csv(unexported)
                
                # Preview
                st.markdown("**Preview (first 5 rows):**")
                st.dataframe(axon_df.head(), use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Download CSV:**")
                
                # Create download
                csv_buffer = io.StringIO()
                axon_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"AXON_Export_{timestamp}.csv"
                
                st.download_button(
                    label="📥 DOWNLOAD AXON CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
                
                st.markdown("---")
                
                # Mark as exported
                st.markdown("**After importing to AXON:**")
                if st.button("✅ Mark All as Exported", use_container_width=True):
                    ticket_numbers = [t.get('TICKET #') for t in unexported]
                    mark_as_exported(ticket_numbers)
                    st.success(f"✅ Marked {len(ticket_numbers)} tickets as exported!")
                    st.cache_data.clear()
                    st.rerun()
                
                st.caption("*Click this after you've imported the CSV into AXON*")
    
    # ============================================================
    # TAB 2: Already Exported
    # ============================================================
    with tab2:
        st.markdown(f"### ✅ Already Exported ({len(exported)})")
        
        if not exported:
            st.info("No tickets have been exported yet.")
        else:
            df_exported = pd.DataFrame(exported)
            display_cols = ['TICKET #', 'DATE', 'CUSTOMER', 'DRIVER', 'ACTUAL VOLUME', 'EXPORTED AT']
            available_cols = [c for c in display_cols if c in df_exported.columns]
            
            st.dataframe(df_exported[available_cols], use_container_width=True, hide_index=True)
            
            # Re-export option
            st.markdown("---")
            st.markdown("**Need to re-export?**")
            
            if st.button("📥 Download All Exported (CSV)", use_container_width=True):
                axon_df = generate_axon_csv(exported)
                csv_buffer = io.StringIO()
                axon_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"AXON_ReExport_{timestamp}.csv",
                    mime="text/csv"
                )
    
    # ============================================================
    # TAB 3: All Tickets
    # ============================================================
    with tab3:
        st.markdown(f"### 📋 All Completed Tickets ({len(all_tickets)})")
        
        df_all = pd.DataFrame(all_tickets)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            customers = ['All'] + list(df_all['CUSTOMER'].unique())
            filter_customer = st.selectbox("Filter by Customer", customers)
        
        with col2:
            drivers = ['All'] + list(df_all['DRIVER'].unique())
            filter_driver = st.selectbox("Filter by Driver", drivers)
        
        with col3:
            export_status = st.selectbox("Export Status", ['All', 'Exported', 'Not Exported'])
        
        # Apply filters
        filtered = df_all.copy()
        
        if filter_customer != 'All':
            filtered = filtered[filtered['CUSTOMER'] == filter_customer]
        
        if filter_driver != 'All':
            filtered = filtered[filtered['DRIVER'] == filter_driver]
        
        if export_status == 'Exported':
            filtered = filtered[filtered['EXPORTED'].str.upper() == 'Y']
        elif export_status == 'Not Exported':
            filtered = filtered[filtered['EXPORTED'].str.upper() != 'Y']
        
        # Display
        display_cols = ['TICKET #', 'DATE', 'CUSTOMER', 'DRIVER', 'PRODUCT', 'ACTUAL VOLUME', 'HOURS', 'EXPORTED']
        available_cols = [c for c in display_cols if c in filtered.columns]
        
        st.dataframe(filtered[available_cols], use_container_width=True, hide_index=True)
        
        # Summary stats
        st.markdown("---")
        st.markdown("### 📈 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tickets", len(filtered))
        
        with col2:
            try:
                total_volume = filtered['ACTUAL VOLUME'].astype(float).sum()
                st.metric("Total Volume", f"{total_volume:,.1f} m³")
            except:
                st.metric("Total Volume", "N/A")
        
        with col3:
            try:
                total_hours = filtered['HOURS'].astype(float).sum()
                st.metric("Total Hours", f"{total_hours:,.1f}")
            except:
                st.metric("Total Hours", "N/A")
        
        with col4:
            exported_count = len(filtered[filtered['EXPORTED'].str.upper() == 'Y'])
            st.metric("Exported", f"{exported_count}/{len(filtered)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <p style='text-align: center; color: gray;'>
    TicketDrop 2.0 | Rick's Oilfield Hauling<br>
    <small>AXON Export Path: C:\\AxonETAAttach\\</small>
    </p>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
