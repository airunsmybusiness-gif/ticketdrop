"""
ticket_pdf_generator.py - Generates _t ticket PDFs for AXON
Matches Rick's Oilfield Hauling ticket format exactly
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="TicketDrop 2.0 - PDF Generator",
    page_icon="📄",
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
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except:
        creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_completed_tickets():
    """Load completed tickets from Google Sheet."""
    try:
        client = get_google_client()
        spreadsheet = client.open("Rick's TicketDrop 2.0")
        worksheet = spreadsheet.worksheet('COMPLETED TICKETS')
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        st.error(f"Error loading tickets: {e}")
        return []

def generate_ticket_pdf(ticket_data):
    """Generate a PDF ticket matching Rick's Oilfield Hauling format."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Starting Y position
    y = height - 50
    
    # === HEADER ===
    # Rick's Oilfield Hauling logo area
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Rick's")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(110, y, "OILFIELD")
    c.drawString(110, y - 15, "HAULING")
    
    # Contact info
    c.setFont("Helvetica", 9)
    c.drawString(250, y, "4606 51 Ave, Redwater, AB")
    c.drawString(250, y - 12, "24 Hour Emergency Number:")
    c.drawString(250, y - 24, "(780) 942-2932")
    
    # Ticket number and date (right side)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(450, y, "Rick's Ticket #")
    c.setFont("Helvetica", 10)
    c.drawString(450, y - 12, str(ticket_data.get('ticket_number', '')))
    c.drawString(450, y - 30, "Date")
    c.drawString(450, y - 42, str(ticket_data.get('date', '')))
    
    y -= 80
    
    # === ASSIGNMENT/VEHICLE DETAILS ===
    c.setFont("Helvetica-Bold", 11)
    c.line(50, y, width - 50, y)
    y -= 15
    c.drawCentredString(width/2, y, "Assignment/Vehicle Details")
    y -= 20
    
    # Vehicle details table
    c.setFont("Helvetica", 9)
    col1, col2, col3, col4 = 50, 200, 350, 480
    
    c.drawString(col1, y, "Operator")
    c.drawString(col2, y, "Truck #")
    c.drawString(col3, y, "Trailer #")
    c.drawString(col4, y, "Company Name")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col1, y, str(ticket_data.get('driver', '')))
    c.drawString(col2, y, str(ticket_data.get('truck', '')))
    c.drawString(col3, y, str(ticket_data.get('trailer', '')))
    c.drawString(col4, y, "Ricks OilField Hauling")
    
    y -= 30
    
    # === TICKET DETAILS ===
    c.setFont("Helvetica-Bold", 11)
    c.line(50, y, width - 50, y)
    y -= 15
    c.drawCentredString(width/2, y, "Ticket Details")
    y -= 25
    
    # Customer info
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Customer Name")
    c.drawString(350, y, "Consignor Address")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, str(ticket_data.get('customer', '')))
    c.drawString(350, y, str(ticket_data.get('consignor_address', '')))
    
    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Location")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    location = f"{ticket_data.get('from_location', '')} To {ticket_data.get('to_location', '')}"
    c.drawString(50, y, location)
    
    y -= 30
    
    # Load/Offload details - two columns
    col_left = 50
    col_right = 320
    
    # LEFT COLUMN - Loading
    c.setFont("Helvetica", 9)
    c.drawString(col_left, y, "Loaded At")
    c.drawString(col_left + 150, y, "Loaded from Tank")
    y_left = y - 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_left, y_left, str(ticket_data.get('from_location', '')))
    c.drawString(col_left + 150, y_left, str(ticket_data.get('load_tank', '')))
    
    # RIGHT COLUMN - Offloading
    c.setFont("Helvetica", 9)
    c.drawString(col_right, y, "Offloaded At")
    c.drawString(col_right + 150, y, "Offloaded into")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_right, y_left, str(ticket_data.get('to_location', '')))
    c.drawString(col_right + 150, y_left, str(ticket_data.get('offload_tank', '')))
    
    y -= 40
    
    # Times
    c.setFont("Helvetica", 9)
    c.drawString(col_left, y, "Arrive - Load Location")
    c.drawString(col_left + 150, y, "Riser")
    c.drawString(col_right, y, "Arrive - Offload Location")
    c.drawString(col_right + 150, y, "Riser")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_left, y, str(ticket_data.get('arrive_load', '')))
    c.drawString(col_left + 150, y, str(ticket_data.get('load_riser', '')))
    c.drawString(col_right, y, str(ticket_data.get('arrive_offload', '')))
    c.drawString(col_right + 150, y, str(ticket_data.get('offload_riser', '')))
    
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(col_left, y, "Depart - Load Location")
    c.drawString(col_right, y, "Depart - Offload Location")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_left, y, str(ticket_data.get('depart_load', '')))
    c.drawString(col_right, y, str(ticket_data.get('depart_offload', '')))
    
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(col_left, y, "Load Start Vol (m3)")
    c.drawString(col_left + 120, y, "Load End Vol (m3)")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_left, y, str(ticket_data.get('load_start_vol', '')))
    c.drawString(col_left + 120, y, str(ticket_data.get('load_end_vol', '')))
    
    y -= 30
    
    # Comments
    c.setFont("Helvetica", 9)
    c.drawString(col_left, y, "Comments")
    c.drawString(col_right, y, "Comments")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_left, y, str(ticket_data.get('load_comments', ''))[:40])
    c.drawString(col_right, y, str(ticket_data.get('offload_comments', ''))[:40])
    
    y -= 30
    
    # === PRODUCT DETAILS ===
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Product")
    c.drawString(300, y, "Last Contained")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, str(ticket_data.get('product', '')))
    c.drawString(300, y, str(ticket_data.get('last_contained', '')))
    
    y -= 25
    
    # Volume and billing details
    c.setFont("Helvetica", 9)
    cols = [50, 130, 210, 290, 370, 450]
    headers = ["Commodity", "Transport Placard", "BS+W (Cut)", "Density", "Road Ban", ""]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    values = [
        str(ticket_data.get('commodity', '')),
        str(ticket_data.get('transport_placard', '')),
        str(ticket_data.get('bsw', '')),
        str(ticket_data.get('density', '')),
        str(ticket_data.get('road_ban', '')),
        ""
    ]
    for i, v in enumerate(values):
        c.drawString(cols[i], y, v[:15])
    
    y -= 25
    
    # Final row
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Estimated Volume")
    c.drawString(150, y, "Actual Volume")
    c.drawString(250, y, "Hours Charged")
    c.drawString(350, y, "Customer Tkt #")
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, str(ticket_data.get('estimated_volume', '')))
    c.drawString(150, y, str(ticket_data.get('actual_volume', '')))
    c.drawString(250, y, str(ticket_data.get('hours_charged', '')))
    c.drawString(350, y, str(ticket_data.get('customer_ticket', '')))
    
    y -= 40
    
    # === HAZARD NOTES ===
    c.line(50, y, width - 50, y)
    y -= 15
    c.setFont("Helvetica", 8)
    c.drawString(50, y, "Hazard at Load: Weather conditions Road in poor condition Spills")
    y -= 10
    c.drawString(50, y, "or potential Slips / trips / falls LOADING/UNLOADING PROCEDURES REVIEWED")
    y -= 15
    c.drawString(50, y, "Hazard at Offload: Weather conditions Road in poor")
    y -= 10
    c.drawString(50, y, "condition Spills or potential Other workers in area Slips / trips")
    y -= 10
    c.drawString(50, y, "/ falls LOADING/UNLOADING PROCEDURES REVIEWED")
    
    # Save PDF
    c.save()
    buffer.seek(0)
    return buffer

# === STREAMLIT UI ===
st.title("📄 TicketDrop 2.0 - PDF Generator")
st.markdown("Generate `_t` ticket PDFs for AXON attachments")

st.divider()

# Load completed tickets
tickets = load_completed_tickets()

if not tickets:
    st.warning("No completed tickets found. Complete some tickets in the Driver app first.")
else:
    st.success(f"Found {len(tickets)} completed tickets")
    
    # Select ticket to generate PDF
    ticket_options = {f"{t.get('ticket_number', 'N/A')} - {t.get('customer', 'Unknown')} ({t.get('date', '')})": t for t in tickets}
    
    selected = st.selectbox("Select a ticket to generate PDF:", list(ticket_options.keys()))
    
    if selected:
        ticket = ticket_options[selected]
        
        # Show ticket preview
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Ticket Details")
            st.write(f"**Ticket #:** {ticket.get('ticket_number', '')}")
            st.write(f"**Date:** {ticket.get('date', '')}")
            st.write(f"**Customer:** {ticket.get('customer', '')}")
            st.write(f"**Driver:** {ticket.get('driver', '')}")
            st.write(f"**Truck:** {ticket.get('truck', '')}")
        
        with col2:
            st.markdown("### Load Details")
            st.write(f"**From:** {ticket.get('from_location', '')}")
            st.write(f"**To:** {ticket.get('to_location', '')}")
            st.write(f"**Product:** {ticket.get('product', '')}")
            st.write(f"**Volume:** {ticket.get('actual_volume', '')} m³")
        
        st.divider()
        
        # Generate PDF button
        if st.button("🔄 Generate PDF", type="primary"):
            with st.spinner("Generating PDF..."):
                pdf_buffer = generate_ticket_pdf(ticket)
                
                ticket_num = ticket.get('ticket_number', 'unknown')
                filename = f"{ticket_num}_t.pdf"
                
                st.success(f"✅ PDF generated: {filename}")
                
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=pdf_buffer,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
                
                st.info("💡 Save this file to `\\\\roh-srv01\\AxonETAAttachments` and AXON will auto-attach it!")

st.divider()

# Bulk generate section
st.markdown("### 📦 Bulk Generate PDFs")
st.markdown("Generate PDFs for all tickets that don't have one yet")

if st.button("Generate All Missing PDFs"):
    if tickets:
        progress = st.progress(0)
        generated = []
        
        for i, ticket in enumerate(tickets):
            pdf_buffer = generate_ticket_pdf(ticket)
            ticket_num = ticket.get('ticket_number', f'ticket_{i}')
            filename = f"{ticket_num}_t.pdf"
            generated.append((filename, pdf_buffer.getvalue()))
            progress.progress((i + 1) / len(tickets))
        
        st.success(f"✅ Generated {len(generated)} PDFs")
        
        # Create download buttons for each
        for filename, pdf_data in generated:
            st.download_button(
                label=f"⬇️ {filename}",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf"
            )
    else:
        st.warning("No tickets to generate")
