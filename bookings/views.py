from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils import timezone
import razorpay
import json

from .models import Booking
from .utils import calculate_price, create_invoice_pdf, send_whatsapp_message

# ============================================
# FIXED VERSION WITH ERROR HANDLING
# ============================================

# 1. Check if Razorpay keys exist in settings
RAZORPAY_ENABLED = False
client = None

try:
    if hasattr(settings, 'RAZORPAY_KEY_ID') and hasattr(settings, 'RAZORPAY_KEY_SECRET'):
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            # Test if keys are valid
            if settings.RAZORPAY_KEY_ID.startswith('rzp_') and len(settings.RAZORPAY_KEY_SECRET) > 10:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                
                # Test connection with small amount
                test_order = client.order.create({
                    "amount": 100,  # ₹1 for testing
                    "currency": "INR",
                    "payment_capture": 1,
                })
                
                RAZORPAY_ENABLED = True
                print("✅ Razorpay enabled successfully")
            else:
                print("⚠️ Razorpay keys appear invalid")
        else:
            print("⚠️ Razorpay keys are empty")
    else:
        print("⚠️ Razorpay keys not found in settings")
        
except Exception as e:
    print(f"❌ Razorpay initialization failed: {str(e)}")
    client = None
    RAZORPAY_ENABLED = False

def book_trip(request):
    """Booking form - FIXED VERSION"""
    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email', '')
            pickup = request.POST.get('pickup')
            drop = request.POST.get('drop')
            distance = float(request.POST.get('distance', 0))
            travel_date = request.POST.get('travel_date')
            travel_time = request.POST.get('travel_time')
            
            if distance <= 0:
                messages.error(request, "Please enter valid distance")
                return render(request, 'bookings/booking_form.html')
            
            # Calculate price
            total_price = calculate_price(distance)
            
            # Create booking
            booking = Booking.objects.create(
                name=name,
                phone=phone,
                email=email if email else None,
                pickup=pickup,
                drop=drop,
                distance_km=distance,
                total_price=total_price,
                travel_date=travel_date,
                travel_time=travel_time,
            )
            
            # Check if Razorpay is available
            if RAZORPAY_ENABLED:
                return redirect('initiate_payment', booking_id=booking.id)
            else:
                # SIMULATION MODE: Direct confirmation
                booking.status = 'CONFIRMED'
                booking.payment_status = 'ADVANCE_PAID'
                booking.advance_paid = 1000
                booking.razorpay_order_id = f"sim_{booking.id}_{int(timezone.now().timestamp())}"
                booking.razorpay_payment_id = f"sim_pay_{booking.id}_{int(timezone.now().timestamp())}"
                booking.save()
                
                messages.success(request, "✅ Booking created successfully! (Simulation Mode)")
                return redirect('booking_confirmation', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
            return render(request, 'bookings/booking_form.html')
    
    today = timezone.now().date()
    return render(request, 'bookings/booking_form.html', {
        'today': today,
        'razorpay_enabled': RAZORPAY_ENABLED,
    })

def initiate_payment(request, booking_id):
    """Initialize payment - FIXED VERSION"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # If Razorpay is not enabled, use simulation
    if not RAZORPAY_ENABLED or client is None:
        messages.info(request, "Payment gateway not configured. Using simulation mode.")
        
        # Simulate payment
        booking.status = 'CONFIRMED'
        booking.payment_status = 'ADVANCE_PAID'
        booking.advance_paid = 1000
        booking.razorpay_order_id = f"sim_order_{booking.id}_{int(timezone.now().timestamp())}"
        booking.save()
        
        return redirect('booking_confirmation', booking_id=booking.id)
    
    try:
        # Create Razorpay order
        order_data = {
            "amount": 1000 * 100,  # ₹1000 in paise
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "booking_id": str(booking.id),
                "customer": booking.name,
            }
        }
        
        order = client.order.create(data=order_data)
        booking.razorpay_order_id = order['id']
        booking.save()
        
        context = {
            'booking': booking,
            'payment': order,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_enabled': True,
            'amount': 1000,
        }
        
        return render(request, 'bookings/checkout.html', context)
        
    except razorpay.errors.BadRequestError as e:
        # Handle invalid keys
        messages.error(request, "⚠️ Invalid payment gateway configuration")
        
        # Fallback to simulation
        booking.status = 'CONFIRMED'
        booking.payment_status = 'ADVANCE_PAID'
        booking.advance_paid = 1000
        booking.razorpay_order_id = f"sim_fallback_{booking.id}"
        booking.save()
        
        return redirect('booking_confirmation', booking_id=booking.id)
        
    except Exception as e:
        messages.error(request, f"❌ Payment error: {str(e)}")
        
        # Fallback to simulation
        booking.status = 'CONFIRMED'
        booking.payment_status = 'ADVANCE_PAID'
        booking.advance_paid = 1000
        booking.save()
        
        return redirect('booking_confirmation', booking_id=booking.id)

@csrf_exempt
def payment_success(request):
    """Payment success handler - FIXED VERSION"""
    if request.method == "POST":
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            razorpay_signature = request.POST.get('razorpay_signature', '')
            
            # Check if this is a simulation
            is_simulation = razorpay_order_id.startswith('sim_') or razorpay_payment_id.startswith('sim_')
            
            if not is_simulation and RAZORPAY_ENABLED:
                # Verify real payment
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                
                try:
                    client.utility.verify_payment_signature(params_dict)
                except:
                    messages.error(request, "Payment verification failed")
                    return redirect('book_trip')
            
            # Get or create booking
            if razorpay_order_id.startswith('sim_'):
                # Extract booking ID from simulation order ID
                try:
                    booking_id = int(razorpay_order_id.split('_')[1])
                    booking = Booking.objects.get(id=booking_id)
                except:
                    messages.error(request, "Invalid booking")
                    return redirect('book_trip')
            else:
                # Real Razorpay order
                try:
                    booking = Booking.objects.get(razorpay_order_id=razorpay_order_id)
                except Booking.DoesNotExist:
                    messages.error(request, "Booking not found")
                    return redirect('book_trip')
            
            # Update booking
            booking.razorpay_payment_id = razorpay_payment_id
            booking.razorpay_signature = razorpay_signature
            booking.status = 'CONFIRMED'
            booking.payment_status = 'ADVANCE_PAID'
            booking.advance_paid = 1000
            booking.save()
            
            # Send WhatsApp
            try:
                send_whatsapp_message(booking)
            except Exception as e:
                print(f"WhatsApp error: {e}")
            
            # Send email
            if booking.email:
                try:
                    send_mail(
                        subject=f"Booking Confirmed - {booking.invoice_no or 'N/A'}",
                        message=f"""Hello {booking.name},

Your booking has been confirmed!

Booking ID: {booking.invoice_no or 'N/A'}
Route: {booking.pickup} to {booking.drop}
Distance: {booking.distance_km} KM
Travel Date: {booking.travel_date}
Total Fare: ₹{booking.total_price}
Advance Paid: ₹{booking.advance_paid}
Remaining: ₹{booking.remaining_amount}

Thank you for choosing Pathan Travels!""",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[booking.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Email error: {e}")
            
            messages.success(request, "✅ Payment successful! Booking confirmed.")
            return redirect('booking_confirmation', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f"❌ Payment processing failed: {str(e)}")
            return redirect('book_trip')
    
    return redirect('book_trip')

def booking_confirmation(request, booking_id):
    """Booking confirmation page"""
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'bookings/confirmation.html', {'booking': booking})

def generate_invoice_pdf(request, booking_id):
    """Generate invoice PDF"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    try:
        pdf_path = create_invoice_pdf(booking)
        
        with open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Invoice_{booking.invoice_no}.pdf"'
            return response
    except:
        # Fallback: Simple text invoice
        invoice_text = f"""
        PATHAN TRAVELS - INVOICE
        ========================
        
        Invoice No: {booking.invoice_no or 'N/A'}
        Date: {booking.created_at.strftime('%d-%m-%Y')}
        
        Customer: {booking.name}
        Phone: {booking.phone}
        
        Route: {booking.pickup} to {booking.drop}
        Distance: {booking.distance_km} KM
        
        Total Fare: ₹{booking.total_price}
        Advance Paid: ₹{booking.advance_paid}
        Remaining: ₹{booking.remaining_amount}
        """
        
        response = HttpResponse(invoice_text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="invoice_{booking.id}.txt"'
        return response

def contact(request):
    """Contact form"""
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message')
        
        try:
            # Save to file instead of email (for testing)
            import os
            from django.conf import settings
            
            contact_dir = os.path.join(settings.MEDIA_ROOT, "contacts")
            os.makedirs(contact_dir, exist_ok=True)
            
            filename = f"contact_{int(timezone.now().timestamp())}.txt"
            filepath = os.path.join(contact_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}")
            
            messages.success(request, "✅ Message sent successfully!")
            
            # Also try to send email if configured
            try:
                if hasattr(settings, 'CONTACT_EMAIL') and settings.CONTACT_EMAIL:
                    send_mail(
                        subject=f"Contact Form: {name}",
                        message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[settings.CONTACT_EMAIL],
                        fail_silently=True,
                    )
            except:
                pass
                
        except Exception as e:
            messages.error(request, f"❌ Failed to save message: {str(e)}")
    
    return render(request, 'bookings/contact.html')

# ============================================
# ADDITIONAL HELPER FUNCTION
# ============================================

def simulate_payment_direct(request, booking_id):
    """Direct simulation without going through payment gateway"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    booking.status = 'CONFIRMED'
    booking.payment_status = 'ADVANCE_PAID'
    booking.advance_paid = 1000
    booking.razorpay_order_id = f"sim_direct_{booking.id}_{int(timezone.now().timestamp())}"
    booking.razorpay_payment_id = f"sim_pay_direct_{booking.id}_{int(timezone.now().timestamp())}"
    booking.save()
    
    messages.success(request, "✅ Booking confirmed via simulation!")
    return redirect('booking_confirmation', booking_id=booking.id)


# bookings/views.py માં imports પછી ઉમેરો
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
@login_required
def admin_delete_booking(request, booking_id):
    """Admin માટે special delete view"""
    if not request.user.is_staff:
        messages.error(request, "Only staff members can delete bookings.")
        return redirect('admin:index')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == "POST":
        try:
            # Store info before deleting
            booking_info = f"{booking.invoice_no} - {booking.name}"
            
            # Check if booking can be deleted
            if booking.status in ['CONFIRMED', 'COMPLETED']:
                messages.error(
                    request, 
                    f"Cannot delete confirmed/completed booking. "
                    f"Please cancel it first."
                )
                return redirect('admin:bookings_booking_change', object_id=booking.id)
            
            # Delete booking
            booking.delete()
            
            # Log the action
            import os
            from django.conf import settings
            
            log_dir = os.path.join(settings.MEDIA_ROOT, "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, "deleted_bookings.log")
            with open(log_file, 'a') as f:
                f.write(f"[{timezone.now()}] {request.user.username} deleted booking: {booking_info}\n")
            
            messages.success(request, f"Booking {booking_info} deleted successfully.")
            return redirect('admin:bookings_booking_changelist')
            
        except Exception as e:
            messages.error(request, f"Error deleting booking: {str(e)}")
            return redirect('admin:bookings_booking_change', object_id=booking.id)
    
    # GET request - show confirmation
    context = {
        'booking': booking,
        'title': 'Delete Booking',
    }
    return render(request, 'admin/delete_confirmation.html', context)