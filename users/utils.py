from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_otp_email(user, otp):
    """Send OTP via email"""
    subject = 'Pathan Travels - Email Verification OTP'
    try:
        html_message = render_to_string('users/email/otp_email.html', {
            'user': user,
            'otp': otp,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Fallback to plain text
        plain_message = f"""
Hello {user.username},

Your OTP for email verification is: {otp}

This code is valid for 10 minutes.

Regards,
Pathan Travels
"""
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

def send_welcome_email(user):
    """Send welcome email after verification"""
    subject = 'Welcome to Pathan Travels!'
    try:
        html_message = render_to_string('users/email/welcome_email.html', {
            'user': user,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        plain_message = f"""
Hello {user.username},

Welcome to Pathan Travels! Your account has been successfully verified.

You can now book trips and view your bookings.

Regards,
Pathan Travels Team
"""
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )