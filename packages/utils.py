# packages/utils.py - COMPLETE FIXED VERSION

import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from django.utils import timezone
from twilio.rest import Client


def send_package_whatsapp_message(booking):
    """Send WhatsApp message for package booking confirmation"""
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        package = booking.package
        site_url = settings.SITE_URL
        pdf_download_url = f"{site_url}/packages/invoice/{booking.id}/"
        
        # ✅ FIXED: Use properties that exist in PackageBooking model
        scheduled_date = booking.scheduled_date if booking.scheduled_date else "Will be confirmed"
        
        if booking.scheduled_time:
            scheduled_time = booking.scheduled_time.strftime('%I:%M %p')
        else:
            scheduled_time = "Will be confirmed"
        
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
            f"🗓 Scheduled Date: {scheduled_date}\n"
            f"⏰ Scheduled Time: {scheduled_time}\n\n"
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
    """Generate WhatsApp URL for package booking"""
    try:
        phone = booking.customer_phone
        package = booking.package
        site_url = settings.SITE_URL
        pdf_download_url = f"{site_url}/packages/invoice/{booking.id}/"
        
        # ✅ FIXED: Use properties that exist
        scheduled_date = booking.scheduled_date if booking.scheduled_date else "Will be confirmed"
        
        if booking.scheduled_time:
            scheduled_time = booking.scheduled_time.strftime('%I:%M %p')
        else:
            scheduled_time = "Will be confirmed"
        
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
            f"🗓 Scheduled Date: {scheduled_date}\n"
            f"⏰ Scheduled Time: {scheduled_time}\n\n"
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


def generate_package_bookings_pdf(bookings, title="Package Bookings Report"):
    """Generate PDF report for package bookings"""
    
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
        "Scheduled Date",  # ✅ CHANGED: Travel Date to Scheduled Date
        "Total Amount",
        "Advance Paid",
        "Remaining",
        "Status"
    ]
    table_data.append(headers)
    
    # Add booking data
    for index, booking in enumerate(bookings, 1):
        # ✅ FIXED: Use scheduled_date instead of travel_date
        date_str = "Not set"
        if booking.scheduled_date:
            date_str = booking.scheduled_date.strftime('%d-%m-%Y')
        
        row = [
            str(index),
            booking.invoice_no or "N/A",
            booking.customer_name,
            booking.customer_phone,
            booking.package.name[:20] + "..." if len(booking.package.name) > 20 else booking.package.name,
            f"{booking.package.pickup_location[:10]}→{booking.package.drop_location[:10]}" if len(booking.package.pickup_location) > 10 else f"{booking.package.pickup_location}→{booking.package.drop_location}",
            str(booking.passengers_count),
            date_str,  # ✅ FIXED: Use scheduled_date
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


# Additional utility functions
def create_package_invoice_pdf(booking):
    """Create PDF invoice for package booking"""
    invoice_dir = os.path.join(settings.MEDIA_ROOT, "invoices/packages")
    os.makedirs(invoice_dir, exist_ok=True)
    
    file_path = os.path.join(invoice_dir, f"package_invoice_{booking.id}.pdf")
    
    p = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 50
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, y, "PATHAN TOURS - PACKAGE INVOICE")
    y -= 40
    
    # Invoice Details
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Invoice No: {booking.invoice_no}")
    p.drawString(350, y, f"Date: {booking.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    y -= 25
    
    # Customer Details
    p.drawString(50, y, f"Customer: {booking.customer_name}")
    y -= 20
    p.drawString(50, y, f"Phone: {booking.customer_phone}")
    if booking.customer_email:
        y -= 20
        p.drawString(50, y, f"Email: {booking.customer_email}")
    y -= 20
    
    # Package Details
    package = booking.package
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Package Details")
    y -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Package: {package.name}")
    y -= 20
    p.drawString(50, y, f"Route: {package.pickup_location} → {package.drop_location}")
    y -= 20
    p.drawString(50, y, f"Distance: {package.distance_km} KM")
    y -= 20
    p.drawString(50, y, f"Duration: {package.duration_days} Day(s)")
    y -= 20
    p.drawString(50, y, f"Vehicle: {package.get_vehicle_type_display()}")
    y -= 20
    p.drawString(50, y, f"Passengers: {booking.passengers_count}")
    
    # ✅ FIXED: Use scheduled_date instead of travel_date
    y -= 20
    if booking.scheduled_date:
        p.drawString(50, y, f"Scheduled Date: {booking.scheduled_date}")
        y -= 20
        if booking.scheduled_time:
            p.drawString(50, y, f"Scheduled Time: {booking.scheduled_time.strftime('%I:%M %p')}")
            y -= 20
    else:
        p.drawString(50, y, f"Schedule: Will be confirmed by admin")
        y -= 20
    
    # Payment Details
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Payment Summary")
    y -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Total Package Fare: ₹{booking.total_amount}")
    y -= 20
    p.drawString(50, y, f"Advance Paid: ₹{booking.advance_paid}")
    y -= 20
    p.drawString(50, y, f"Remaining Amount: ₹{booking.remaining_amount}")
    
    p.showPage()
    p.save()
    
    return file_path