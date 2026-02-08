import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings
from twilio.rest import Client

def calculate_price(distance_km, is_festival=False):
    rate_per_km = 16 if is_festival else 14
    return int(distance_km * rate_per_km)

# bookings/utils.py
import os
import requests
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from twilio.rest import Client

def send_whatsapp_message(booking):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # PDF બનાવો
        pdf_path = create_invoice_pdf(booking)
        
        # Site URL (તમારું વેબસાઈટ URL)
        site_url = settings.SITE_URL
        
        # PDF ડાઉનલોડ લિંક
        pdf_download_url = f"{site_url}/book/invoice/{booking.id}/"
        
        msg = (
            f"Hello {booking.name} 👋\n\n"
            f"Your booking is CONFIRMED ✅\n\n"
            f"📋 Booking ID: {booking.invoice_no}\n"
            f"📍 Route: {booking.pickup} → {booking.drop}\n"
            f"📏 Distance: {booking.distance_km} KM\n"
            f"🗓 Travel Date: {booking.travel_date}\n"
            f"⏰ Travel Time: {booking.travel_time.strftime('%I:%M %p')}\n\n"
            f"💰 Total Fare: ₹{booking.total_price}\n"
            f"💵 Advance Paid: ₹{booking.advance_paid}\n"
            f"💳 Remaining Amount: ₹{booking.remaining_amount}\n\n"
            f"📄 Invoice Download: {pdf_download_url}\n\n"
            f"Pathan Tours & Travels 🚗\n"
            f"📞 9879230065\n"
            f"📍 Download invoice from above link"
        )
        
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:+91{booking.phone}",
            body=msg
        )
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        
        # Alternative: WhatsApp business API નો ઉપયોગ કરો
        send_whatsapp_via_url(booking)
        return False

def send_whatsapp_via_url(booking):
    """WhatsApp લિંક દ્વારા મેસેજ મોકલવું"""
    try:
        phone = booking.phone
        site_url = settings.SITE_URL
        pdf_download_url = f"{site_url}/book/invoice/{booking.id}/"
        
        message = (
            f"Hello {booking.name} 👋\n\n"
            f"Your booking is CONFIRMED ✅\n\n"
            f"📋 Booking ID: {booking.invoice_no}\n"
            f"📍 Route: {booking.pickup} → {booking.drop}\n"
            f"📏 Distance: {booking.distance_km} KM\n"
            f"🗓 Travel Date: {booking.travel_date}\n"
            f"⏰ Travel Time: {booking.travel_time.strftime('%I:%M %p')}\n\n"
            f"💰 Total Fare: ₹{booking.total_price}\n"
            f"💵 Advance Paid: ₹{booking.advance_paid}\n"
            f"💳 Remaining Amount: ₹{booking.remaining_amount}\n\n"
            f"📄 Invoice: {pdf_download_url}"
        )
        
        # WhatsApp લિંક બનાવો
        whatsapp_url = f"https://api.whatsapp.com/send?phone=91{phone}&text={message}"
        
        # લિંક કોપી કરવા માટે (Admin માં બતાવવા)
        print(f"WhatsApp Link: {whatsapp_url}")
        
        return whatsapp_url
    except Exception as e:
        print(f"WhatsApp URL error: {e}")
        return None

def create_invoice_pdf(booking):
    invoice_dir = os.path.join(settings.MEDIA_ROOT, "invoices")
    os.makedirs(invoice_dir, exist_ok=True)
    
    file_path = os.path.join(invoice_dir, f"invoice_{booking.id}.pdf")
    
    p = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 50
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, y, "PATHAN TRAVELS - INVOICE")
    y -= 40
    
    # Invoice Details
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Invoice No: {booking.invoice_no}")
    p.drawString(350, y, f"Date: {booking.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    y -= 25
    
    # Customer Details
    p.drawString(50, y, f"Customer: {booking.name}")
    y -= 20
    p.drawString(50, y, f"Phone: {booking.phone}")
    if booking.email:
        y -= 20
        p.drawString(50, y, f"Email: {booking.email}")
    y -= 20
    
    # Trip Details
    p.drawString(50, y, f"Pickup: {booking.pickup}")
    y -= 20
    p.drawString(50, y, f"Drop: {booking.drop}")
    y -= 20
    p.drawString(50, y, f"Distance: {booking.distance_km} KM")
    y -= 20
    
    # Travel Date/Time
    p.drawString(50, y, f"Travel Date: {booking.travel_date}")
    y -= 20
    p.drawString(50, y, f"Travel Time: {booking.travel_time.strftime('%I:%M %p')}")
    y -= 20
    
    # Payment Details
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Payment Summary")
    y -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Total Fare: ₹{booking.total_price}")
    y -= 20
    p.drawString(50, y, f"Advance Paid: ₹{booking.advance_paid}")
    y -= 20
    p.drawString(50, y, f"Remaining Amount: ₹{booking.remaining_amount}")
    
    # Contact Information
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Contact Information")
    y -= 20
    
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Pathan Tours & Travels")
    y -= 15
    p.drawString(50, y, "Phone: 9879230065, 9925993770")
    y -= 15
    p.drawString(50, y, "Email: pathanashif124@gmail.com")
    
    p.showPage()
    p.save()
    
    return file_path