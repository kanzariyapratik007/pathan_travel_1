# core/views.py
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message')
        
        # Send email to admin
        subject = f'New Contact Message from {name}'
        body = f"""
        Name: {name}
        Email: {email}
        Phone: {phone}
        Message: {message}
        """
        
        try:
            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('contact')
        except Exception as e:
            messages.error(request, f'Failed to send message. Error: {str(e)}')
            return redirect('contact')
    
    return render(request, 'core/contact.html')

# Note: 'contact_view' નામ નથી, 'contact' છે