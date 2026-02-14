from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.conf import settings

from .forms import UserRegistrationForm, UserLoginForm, OTPVerificationForm
from .models import User, UserProfile
from .utils import send_otp_email, send_welcome_email
from packages.models import PackageBooking
from bookings.models import Booking

def register_view(request):
    """User Registration - Step 1: Email & Password"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verification
            user.save()
            
            # Generate and send OTP
            otp = user.generate_otp()
            send_otp_email(user, otp)
            
            # Store user ID in session for OTP verification
            request.session['pending_user_id'] = user.id
            
            messages.success(request, 'Registration successful! Please verify your email with the OTP sent.')
            return redirect('verify_otp')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def verify_otp_view(request):
    """Step 2: Verify Email OTP"""
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('register')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please register again.')
        return redirect('register')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            if user.verify_otp(entered_otp):
                user.is_email_verified = True
                user.is_active = True
                user.otp = None
                user.otp_created_at = None
                user.save()
                
                # Create user profile
                UserProfile.objects.get_or_create(user=user)
                
                # Send welcome email
                send_welcome_email(user)
                
                # Auto login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Clear session
                del request.session['pending_user_id']
                
                messages.success(request, 'Email verified successfully! Welcome to Pathan Travels!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'users/verify_otp.html', {
        'form': form,
        'user_email': user.email
    })


def resend_otp_view(request):
    """Resend OTP email"""
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('register')
    
    try:
        user = User.objects.get(id=user_id)
        otp = user.generate_otp()
        send_otp_email(user, otp)
        messages.success(request, 'New OTP has been sent to your email.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('verify_otp')


def login_view(request):
    """User Login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_email_verified:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    
                    # Redirect to next page if exists
                    next_page = request.GET.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect('home')
                else:
                    messages.warning(request, 'Please verify your email first. Check your inbox for OTP.')
                    
                    # Regenerate OTP and send
                    otp = user.generate_otp()
                    send_otp_email(user, otp)
                    
                    request.session['pending_user_id'] = user.id
                    return redirect('verify_otp')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please enter valid credentials.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """User Logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """User Profile"""
    user = request.user
    
    # Get user's bookings
    package_bookings = PackageBooking.objects.filter(
        customer_email=user.email
    ).order_by('-created_at')[:10]
    
    one_way_bookings = Booking.objects.filter(
        email=user.email
    ).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'package_bookings': package_bookings,
        'one_way_bookings': one_way_bookings,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit User Profile"""
    user = request.user
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        # Update user info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        # Update profile
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.pincode = request.POST.get('pincode', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'users/edit_profile.html', {
        'user': user,
        'profile': profile
    })


from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from bookings.models import Booking
from packages.models import PackageBooking

@login_required
def my_bookings_view(request):
    """View all bookings - Email અને Phone બંનેથી શોધો"""
    user = request.user
    
    # Debug print
    print(f"🔍 User: {user.email}, Phone: {user.phone}")
    
    # 1. One-way Bookings - Email અને Phone બંનેથી શોધો
    one_way_bookings = Booking.objects.none()  # Empty queryset
    
    if user.email:
        email_bookings = Booking.objects.filter(email=user.email)
        one_way_bookings = email_bookings
        print(f"📧 Email bookings: {email_bookings.count()}")
    
    if user.phone:
        phone_bookings = Booking.objects.filter(phone=user.phone)
        print(f"📞 Phone bookings: {phone_bookings.count()}")
        
        # Merge with email bookings
        if one_way_bookings.exists():
            one_way_bookings = (email_bookings | phone_bookings).distinct()
        else:
            one_way_bookings = phone_bookings
    
    # 2. Package Bookings - Email અને Phone બંનેથી શોધો
    package_bookings = PackageBooking.objects.none()
    
    if user.email:
        email_package = PackageBooking.objects.filter(customer_email=user.email)
        package_bookings = email_package
    
    if user.phone:
        phone_package = PackageBooking.objects.filter(customer_phone=user.phone)
        if package_bookings.exists():
            package_bookings = (email_package | phone_package).distinct()
        else:
            package_bookings = phone_package
    
    # Order by latest
    one_way_bookings = one_way_bookings.order_by('-created_at')
    package_bookings = package_bookings.order_by('-created_at')
    
    context = {
        'one_way_bookings': one_way_bookings,
        'package_bookings': package_bookings,
        'user_email': user.email,
        'user_phone': user.phone,
        'one_way_count': one_way_bookings.count(),
        'package_count': package_bookings.count(),
    }
    
    return render(request, 'users/my_bookings.html', context)


@login_required
def change_password_view(request):
    """Change Password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = request.user
        
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password changed successfully! Please login again.')
            return redirect('login')
    
    return render(request, 'users/change_password.html')