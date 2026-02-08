# packages/utils.py (નવું ફાઈલ બનાવો)
import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from twilio.rest import Client

def send_package_whatsapp_message(booking):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        package = booking.package
        site_url = settings.SITE_URL
        pdf_download_url = f"{site_url}/packages/invoice/{booking.id}/"
        
        msg = (
            f"Hello {booking.customer_name} 👋\n\n"
            f"✨ **Package Booking Confirmed!** ✨\n\n"
            f"📦 Package: {package.name}\n"
            f"📋 Booking ID: {booking.invoice_no}\n"
            f"📍 Route: {package.pickup_location} → {package.drop_location}\n"
            f"📏 Distance: {package.distance_km} KM\n"
            f"⏳ Duration: {package.duration_days} Day(s)\n"
            f"🚗 Vehicle: {package.get_vehicle_type_display()}\n"
            f"👥 Passengers: {booking.passengers_count}\n"
            f"🗓 Travel Date: {booking.travel_date}\n"
            f"⏰ Travel Time: {booking.travel_time.strftime('%I:%M %p')}\n\n"
            f"💰 Total Fare: ₹{booking.total_amount}\n"
            f"💵 Advance Paid: ₹{booking.advance_paid}\n"
            f"💳 Remaining: ₹{booking.remaining_amount}\n\n"
            f"📄 Invoice Download: {pdf_download_url}\n\n"
            f"✅ **Package Inclusions:**\n"
            f"{package.inclusions}\n\n"
            f"📝 **Important Notes:**\n"
            f"{package.important_notes}\n\n"
            f"Thank you for choosing Pathan Travels! 🚗\n"
            f"Need help? Call: 9879230065"
        )
        
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:+91{booking.customer_phone}",
            body=msg
        )
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        
        # Alternative method
        send_package_whatsapp_via_url(booking)
        return False

def send_package_whatsapp_via_url(booking):
    """Package booking માટે WhatsApp લિંક"""
    try:
        phone = booking.customer_phone
        package = booking.package
        site_url = settings.SITE_URL
        pdf_download_url = f"{site_url}/packages/invoice/{booking.id}/"
        
        message = (
            f"Hello {booking.customer_name} 👋\n\n"
            f"Package Booking Confirmed! ✅\n\n"
            f"📦 Package: {package.name}\n"
            f"📋 Booking ID: {booking.invoice_no}\n"
            f"📍 Route: {package.pickup_location} → {package.drop_location}\n"
            f"📏 Distance: {package.distance_km} KM\n"
            f"⏳ Duration: {package.duration_days} Day(s)\n"
            f"🚗 Vehicle: {package.get_vehicle_type_display()}\n"
            f"👥 Passengers: {booking.passengers_count}\n"
            f"🗓 Travel Date: {booking.travel_date}\n"
            f"⏰ Travel Time: {booking.travel_time.strftime('%I:%M %p')}\n\n"
            f"💰 Total Fare: ₹{booking.total_amount}\n"
            f"💵 Advance Paid: ₹{booking.advance_paid}\n"
            f"💳 Remaining: ₹{booking.remaining_amount}\n\n"
            f"📄 Invoice: {pdf_download_url}"
        )
        
        whatsapp_url = f"https://api.whatsapp.com/send?phone=91{phone}&text={message}"
        print(f"Package WhatsApp Link: {whatsapp_url}")
        
        return whatsapp_url
    except Exception as e:
        print(f"Package WhatsApp URL error: {e}")
        return None
    
    # packages/utils.py માં નીચેના ફંકશન ઉમેરો
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from django.conf import settings
from django.utils import timezone

def generate_package_bookings_pdf(bookings, title="Package Bookings Report"):
    """Package bookings ની list PDF માં બનાવવી"""
    
    # Create directory if not exists
    pdf_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Generate filename
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"package_bookings_{timestamp}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    # Create PDF
    p = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 50, "PATHAN TOURS & TRAVELS")
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, height - 75, title)
    
    # Report Info
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 100, f"Generated on: {timezone.now().strftime('%d-%m-%Y %H:%M:%S')}")
    p.drawString(width - 200, height - 100, f"Total Bookings: {len(bookings)}")
    
    # Table data
    table_data = []
    
    # Table headers
    headers = [
        "Sr.No",
        "Booking ID",
        "Customer Name",
        "Phone",
        "Package",
        "Route",
        "Passengers",
        "Travel Date",
        "Total Amount",
        "Advance Paid",
        "Remaining",
        "Status"
    ]
    table_data.append(headers)
    
    # Add booking data
    for index, booking in enumerate(bookings, 1):
        row = [
            str(index),
            booking.invoice_no or "N/A",
            booking.customer_name,
            booking.customer_phone,
            booking.package.name[:20] + "..." if len(booking.package.name) > 20 else booking.package.name,
            f"{booking.package.pickup_location[:10]}→{booking.package.drop_location[:10]}" if len(booking.package.pickup_location) > 10 else f"{booking.package.pickup_location}→{booking.package.drop_location}",
            str(booking.passengers_count),
            booking.travel_date.strftime('%d-%m-%Y'),
            f"₹{booking.total_amount}",
            f"₹{booking.advance_paid}",
            f"₹{booking.remaining_amount}",
            booking.get_status_display()
        ]
        table_data.append(row)
    
    # Create table
    table = Table(table_data, colWidths=[0.4*inch, 1.2*inch, 1.0*inch, 0.8*inch, 1.0*inch, 
                                         1.2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 
                                         0.8*inch, 0.8*inch])
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    
    # Draw table on PDF
    table.wrapOn(p, width - 100, height)
    table.drawOn(p, 50, height - 450)
    
    # Summary
    y_position = height - 480
    
    # Calculate totals
    total_amount = sum(booking.total_amount for booking in bookings)
    total_advance = sum(booking.advance_paid for booking in bookings)
    total_remaining = sum(booking.remaining_amount for booking in bookings)
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "SUMMARY:")
    y_position -= 20
    
    p.setFont("Helvetica", 9)
    p.drawString(50, y_position, f"Total Bookings: {len(bookings)}")
    p.drawString(200, y_position, f"Total Amount: ₹{total_amount}")
    p.drawString(350, y_position, f"Total Advance: ₹{total_advance}")
    p.drawString(500, y_position, f"Total Remaining: ₹{total_remaining}")
    
    # Status Count
    y_position -= 30
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "STATUS COUNT:")
    y_position -= 20
    
    status_counts = {}
    for booking in bookings:
        status = booking.get_status_display()
        status_counts[status] = status_counts.get(status, 0) + 1
    
    col = 0
    for status, count in status_counts.items():
        x_position = 50 + (col * 150)
        p.setFont("Helvetica", 9)
        p.drawString(x_position, y_position, f"{status}: {count}")
        col += 1
        if col > 3:
            col = 0
            y_position -= 15
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 50, "Generated by Pathan Tours & Travels Admin Panel")
    p.drawCentredString(width/2, 40, f"Page 1 of 1")
    
    p.showPage()
    p.save()
    
    return filepath, filename