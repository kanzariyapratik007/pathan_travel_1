# packages/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils import timezone

from .models import Package, PackageBooking
import razorpay
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from twilio.rest import Client

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def package_list(request):
    packages = Package.objects.filter(is_active=True)
    return render(request, 'packages/package_list.html', {'packages': packages})

def package_detail(request, package_id):
    package = get_object_or_404(Package, id=package_id, is_active=True)
    
    if request.method == "POST":
        try:
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')
            customer_email = request.POST.get('customer_email', '')
            travel_date = request.POST.get('travel_date')
            travel_time = request.POST.get('travel_time')
            passengers_count = int(request.POST.get('passengers_count', 1))
            special_requirements = request.POST.get('special_requirements', '')
            
            # Create package booking
            booking = PackageBooking.objects.create(
                package=package,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email if customer_email else None,
                travel_date=travel_date,
                travel_time=travel_time,
                passengers_count=passengers_count,
                special_requirements=special_requirements,
                total_amount=package.final_price,
                advance_paid=package.advance_amount,
            )
            
            return redirect('package_payment', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('package_detail', package_id=package_id)
    
    today = timezone.now().date()
    return render(request, 'packages/package_detail.html', {
        'package': package,
        'today': today,
    })

def package_payment(request, booking_id):
    booking = get_object_or_404(PackageBooking, id=booking_id)
    
    try:
        order_data = {
            "amount": booking.advance_paid * 100,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "booking_id": str(booking.id),
                "invoice_no": booking.invoice_no,
                "package_name": booking.package.name
            }
        }
        
        order = client.order.create(data=order_data)
        booking.razorpay_order_id = order['id']
        booking.save()
        
        context = {
            'booking': booking,
            'payment': order,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        }
        
        return render(request, 'packages/checkout.html', context)
        
    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('package_detail', package_id=booking.package.id)

@csrf_exempt
def package_payment_success(request):
    if request.method == "POST":
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            booking = PackageBooking.objects.get(razorpay_order_id=razorpay_order_id)
            booking.razorpay_payment_id = razorpay_payment_id
            booking.razorpay_signature = razorpay_signature
            booking.status = 'CONFIRMED'
            booking.payment_status = 'ADVANCE_PAID'
            booking.save()
            
            # Send WhatsApp message
            send_package_whatsapp_message(booking)
            
            # Send email confirmation
            if booking.customer_email:
                send_package_confirmation_email(booking)
            
            messages.success(request, "Payment successful! Package booking confirmed.")
            return redirect('package_booking_confirmation', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('package_list')
    
    return redirect('package_list')

def package_booking_confirmation(request, booking_id):
    booking = get_object_or_404(PackageBooking, id=booking_id)
    return render(request, 'packages/confirmation.html', {'booking': booking})

def package_invoice(request, booking_id):  # Fixed function name
    booking = get_object_or_404(PackageBooking, id=booking_id)
    pdf_path = create_package_invoice_pdf(booking)
    
    with open(pdf_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Package_Invoice_{booking.invoice_no}.pdf"'
        return response

# Utility functions
def send_package_whatsapp_message(booking):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        package = booking.package
        
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
        return False

def send_package_confirmation_email(booking):
    try:
        package = booking.package
        
        subject = f"Package Booking Confirmed - {booking.invoice_no}"
        
        message = f"""
Dear {booking.customer_name},

Your package tour has been confirmed successfully!

**Booking Details:**
Booking ID: {booking.invoice_no}
Package: {package.name}
Route: {package.pickup_location} to {package.drop_location}
Distance: {package.distance_km} KM
Duration: {package.duration_days} Day(s)
Vehicle: {package.get_vehicle_type_display()}
Passengers: {booking.passengers_count}
Travel Date: {booking.travel_date}
Travel Time: {booking.travel_time.strftime('%I:%M %p')}

**Payment Summary:**
Total Fare: ₹{booking.total_amount}
Advance Paid: ₹{booking.advance_paid}
Remaining Amount: ₹{booking.remaining_amount}

**Package Inclusions:**
{package.inclusions}

**Important Notes:**
{package.important_notes}

**Special Requirements:**
{booking.special_requirements if booking.special_requirements else 'None'}

For any queries, please contact us at 9879230065.

Thank you for choosing Pathan Tours & Travels!

Best regards,
Pathan Tours Team
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.customer_email],
            fail_silently=True,
        )
        return True
    except:
        return False

def create_package_invoice_pdf(booking):
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
    y -= 20
    p.drawString(50, y, f"Travel Date: {booking.travel_date}")
    y -= 20
    p.drawString(50, y, f"Travel Time: {booking.travel_time.strftime('%I:%M %p')}")
    
    # Payment Details
    y -= 20
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

# packages/views.py માં નીચેના imports ઉમેરો
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import PackageBooking
from .utils import generate_package_bookings_pdf
import json

# Admin check function
def is_admin_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin_user)
def admin_package_bookings_pdf(request):
    """Admin માટે package bookings ની PDF"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    package_id = request.GET.get('package', '')
    
    # Start with all bookings
    bookings = PackageBooking.objects.all().select_related('package')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if date_from:
        bookings = bookings.filter(created_at__date__gte=date_from)
    
    if date_to:
        bookings = bookings.filter(created_at__date__lte=date_to)
    
    if package_id:
        bookings = bookings.filter(package_id=package_id)
    
    # Order by latest
    bookings = bookings.order_by('-created_at')
    
    # Generate title
    title = "Package Bookings Report"
    if status_filter:
        title += f" - Status: {dict(PackageBooking.STATUS_CHOICES).get(status_filter, status_filter)}"
    if date_from and date_to:
        title += f" - From {date_from} to {date_to}"
    
    # Generate PDF
    pdf_path, filename = generate_package_bookings_pdf(bookings, title)
    
    # Return PDF as response
    with open(pdf_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

@login_required
@user_passes_test(is_admin_user)
def admin_package_bookings_report(request):
    """Admin report page"""
    from .models import Package
    
    # Get all packages for filter
    packages = Package.objects.all()
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    package_id = request.GET.get('package', '')
    
    # Start with all bookings
    bookings = PackageBooking.objects.all().select_related('package')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if date_from:
        bookings = bookings.filter(created_at__date__gte=date_from)
    
    if date_to:
        bookings = bookings.filter(created_at__date__lte=date_to)
    
    if package_id:
        bookings = bookings.filter(package_id=package_id)
    
    # Order by latest
    bookings = bookings.order_by('-created_at')
    
    # Calculate totals
    total_bookings = bookings.count()
    total_amount = sum(b.total_amount for b in bookings) if bookings else 0
    total_advance = sum(b.advance_paid for b in bookings) if bookings else 0
    total_remaining = sum(b.remaining_amount for b in bookings) if bookings else 0
    
    # Status counts
    status_counts = {}
    for status_code, status_name in PackageBooking.STATUS_CHOICES:
        count = bookings.filter(status=status_code).count()
        if count > 0:
            status_counts[status_name] = count
    
    context = {
        'bookings': bookings,
        'packages': packages,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'package_id': int(package_id) if package_id else '',
        'total_bookings': total_bookings,
        'total_amount': total_amount,
        'total_advance': total_advance,
        'total_remaining': total_remaining,
        'status_counts': status_counts,
        'status_choices': PackageBooking.STATUS_CHOICES,
    }
    
    return render(request, 'admin/package_bookings_report.html', context)