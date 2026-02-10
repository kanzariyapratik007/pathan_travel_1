# packages/admin.py - COMPLETE FIXED VERSION

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from .models import Package, PackageBooking
from datetime import datetime, date
import urllib.parse


# ============ CUSTOM FORM FOR DATE/TIME VALIDATION ============
class PackageAdminForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = '__all__'
    
    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date:
            # Check if date is not in the past
            if scheduled_date < date.today():
                raise forms.ValidationError("Travel date cannot be in the past!")
        return scheduled_date
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Date field widget
        if 'scheduled_date' in self.fields:
            self.fields['scheduled_date'].widget = forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'vDateField',
                    'placeholder': 'YYYY-MM-DD'
                }
            )
        
        # Time field widget
        if 'scheduled_time' in self.fields:
            self.fields['scheduled_time'].widget = forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'vTimeField',
                    'placeholder': 'HH:MM'
                }
            )


# ============ PACKAGE BOOKING ACTIONS ============
@admin.action(description="🗑️ Delete selected package bookings")
def delete_package_bookings(modeladmin, request, queryset):
    """Delete multiple package bookings"""
    
    # Check for confirmed/completed bookings
    confirmed_bookings = queryset.filter(status__in=['CONFIRMED', 'COMPLETED'])
    if confirmed_bookings.exists():
        messages.error(
            request, 
            f"Cannot delete {confirmed_bookings.count()} confirmed/completed bookings. "
            f"Please cancel them first."
        )
        return
    
    count = queryset.count()
    if count > 5:
        messages.warning(
            request, 
            f"You are about to delete {count} package bookings. This action cannot be undone!"
        )
    
    deleted_count, _ = queryset.delete()
    messages.success(
        request, 
        f"Successfully deleted {deleted_count} package booking(s)."
    )


@admin.action(description="❌ Cancel selected package bookings")
def cancel_package_bookings(modeladmin, request, queryset):
    """Cancel multiple package bookings"""
    for booking in queryset:
        booking.status = 'CANCELLED'
        booking.payment_status = 'PENDING'
        booking.save()
    
    count = queryset.count()
    messages.success(
        request, 
        f"Successfully cancelled {count} package booking(s)."
    )


# packages/admin.py - FIX THE send_package_whatsapp FUNCTION

@admin.action(description="📱 Send WhatsApp for packages")
# packages/admin.py - UPDATE THE send_package_whatsapp FUNCTION

@admin.action(description="📱 Send WhatsApp for packages")
def send_package_whatsapp(modeladmin, request, queryset):
    """Send WhatsApp message for package bookings"""
    
    for booking in queryset:
        package = booking.package
        
        # Use scheduled_date and scheduled_time
        scheduled_date = booking.scheduled_date if booking.scheduled_date else "Will be confirmed"
        
        # Format time if exists
        if booking.scheduled_time:
            scheduled_time = booking.scheduled_time.strftime('%I:%M %p')
        else:
            scheduled_time = "Will be confirmed"
        
        msg = f"""Hello {booking.customer_name} 👋

✨ **Package Booking Confirmed!** ✨

📦 Package: {package.name}
📋 Booking ID: {booking.invoice_no}
📍 Route: {package.pickup_location} → {package.drop_location}
📏 Distance: {package.distance_km} KM
⏳ Duration: {package.duration_days} Day(s)
🚗 Vehicle: {package.get_vehicle_type_display()}
👥 Passengers: {booking.passengers_count}
🗓 **Scheduled Date:** {scheduled_date}
⏰ **Scheduled Time:** {scheduled_time}

💰 Total Fare: ₹{booking.total_amount}
💵 Advance Paid: ₹{booking.advance_paid}
💳 Remaining: ₹{booking.remaining_amount}

Thank you for choosing Pathan Travels! 🚗"""
        
        whatsapp_url = f"https://wa.me/91{booking.customer_phone}?text={urllib.parse.quote(msg)}"
        
        messages.info(
            request, 
            format_html(
                f'WhatsApp for {booking.customer_name}: '
                f'<a href="{whatsapp_url}" target="_blank" style="color: #25D366; font-weight: bold;">Click here</a>'
            )
        )


# ============ PACKAGE ADMIN ============
@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageAdminForm
    
    list_display = (
        'name',
        'package_type',
        'route_display',
        'scheduled_date',
        'get_formatted_scheduled_time',
        'distance_km',
        'duration_days',
        'vehicle_type',
        'base_price',
        'final_price_display',
        'is_active',
        'created_at',
        'package_actions_column',
    )
    
    list_filter = (
        'package_type', 
        'vehicle_type', 
        'is_active', 
        'is_festival_rate', 
        'scheduled_date',
        'created_at',
    )
    
    search_fields = (
        'name', 
        'pickup_location', 
        'drop_location', 
        'description',
        'inclusions',
        'exclusions',
    )
    
    list_per_page = 20
    
    def get_readonly_fields(self, request, obj=None):
        readonly = ['created_at', 'updated_at', 'package_delete_button', 'final_price_display',]
        if obj:  # Editing an existing object
            return readonly + ['final_price_display']
        return readonly  # Creating a new object
    
    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'package_type', 'description', 'is_active')
        }),
        ('Schedule (Set by Admin)', {
            'fields': ('scheduled_date', 'scheduled_time'),
            'description': 'Date and time for this package. Customers cannot change these.'
        }),
        ('Route Details', {
            'fields': ('pickup_location', 'drop_location', 'distance_km', 'duration_days')
        }),
        ('Vehicle Details', {
            'fields': ('vehicle_type', 'max_passengers')
        }),
        ('Pricing', {
            'fields': ('base_price', 'advance_amount', 'is_festival_rate', 'final_price_display'),
            'description': 'Base price will increase by 15% during festival rates'
        }),
        ('Images', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('Inclusions & Exclusions', {
            'fields': ('inclusions', 'exclusions'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('important_notes',),
            'classes': ('collapse',)
        }),
        ('Danger Zone', {
            'fields': ('package_delete_button',),
            'classes': ('collapse',),
            'description': 'Package deletion - Use with caution'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Date field setup
        form.base_fields['scheduled_date'].help_text = "Format: YYYY-MM-DD (e.g., 2026-03-05)"
        form.base_fields['scheduled_date'].required = False
        form.base_fields['scheduled_date'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'vDateField',
                'style': 'width: 200px;',
                'placeholder': 'YYYY-MM-DD'
            }
        )
        
        # Time field setup
        form.base_fields['scheduled_time'].help_text = "Format: HH:MM (24-hour, e.g., 17:30 for 5:30 PM)"
        form.base_fields['scheduled_time'].required = False
        form.base_fields['scheduled_time'].widget = forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'vTimeField',
                'style': 'width: 150px;',
                'placeholder': 'HH:MM'
            }
        )
        
        # Image field help text
        form.base_fields['cover_image'].help_text = "Recommended size: 800x400px"
        
        return form
    
    def route_display(self, obj):
        return f"{obj.pickup_location} → {obj.drop_location}"
    route_display.short_description = 'Route'
    route_display.admin_order_field = 'pickup_location'
    
    def get_formatted_scheduled_time(self, obj):
        if obj.scheduled_time:
            return obj.scheduled_time.strftime('%I:%M %p')
        return "Not set"
    get_formatted_scheduled_time.short_description = 'Scheduled Time'
    
    def final_price_display(self, obj):
        if obj.is_festival_rate:
            return f"₹{int(obj.base_price * 1.15)} (Festival)"
        return f"₹{obj.base_price}"
    final_price_display.short_description = 'Final Price'
    
    def package_actions_column(self, obj):
        """Actions column in package list"""
        change_url = reverse('admin:packages_package_change', args=[obj.id])
        delete_url = reverse('admin:packages_package_delete', args=[obj.id])
        
        # Check if package has any bookings
        has_bookings = obj.bookings.exists()
        
        if has_bookings:
            delete_button = format_html(
                '<span style="color:#6c757d;font-size:11px;" title="Cannot delete - Has bookings">'
                '<i class="fas fa-lock"></i> Locked</span>'
            )
        else:
            delete_button = format_html(
                f'<a href="{delete_url}" class="button" '
                'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;" '
                f'onclick="return confirm(\'Delete package {obj.name}?\')">'
                '<i class="fas fa-trash"></i> Delete</a>'
            )
        
        return format_html(
            f'<div style="display: flex; gap: 5px;">'
            f'<a href="{change_url}" class="button" style="background:#198754;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;">'
            f'<i class="fas fa-edit"></i> Edit</a>'
            f'{delete_button}'
            f'</div>'
        )
    package_actions_column.short_description = 'Actions'
    
    def package_delete_button(self, obj):
        """Delete button in package edit form"""
        if not obj.id:
            return "Save package first to see delete option"
        
        delete_url = reverse('admin:packages_package_delete', args=[obj.id])
        
        # Check if package has bookings
        has_bookings = obj.bookings.exists()
        
        if has_bookings:
            booking_count = obj.bookings.count()
            return format_html(
                '<div style="background:#fff3cd;padding:15px;border-radius:5px;border:1px solid #ffeaa7;">'
                '<h4 style="color:#856404;margin-top:0;"><i class="fas fa-lock"></i> Cannot Delete Package</h4>'
                f'<p style="color:#856404;">This package has <strong>{booking_count} booking(s)</strong>. '
                f'You must delete all bookings first before deleting the package.</p>'
                f'<p><a href="../packagebooking/?package__id__exact={obj.id}" style="color:#198754;">'
                f'<i class="fas fa-external-link-alt"></i> View Package Bookings</a></p>'
                f'</div>'
            )
        else:
            return format_html(
                '<div style="background:#f8d7da;padding:15px;border-radius:5px;border:1px solid #f5c6cb;">'
                '<h4 style="color:#721c24;margin-top:0;"><i class="fas fa-exclamation-triangle"></i> Danger Zone</h4>'
                '<p style="color:#721c24;">This action will permanently delete the package.</p>'
                f'<p><strong>Package:</strong> {obj.name}</p>'
                f'<p><strong>Route:</strong> {obj.pickup_location} → {obj.drop_location}</p>'
                f'<a href="{delete_url}" class="button" '
                'style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;" '
                f'onclick="return confirm(\'Are you absolutely sure?\\n\\nPackage: {obj.name}\\nRoute: {obj.pickup_location} → {obj.drop_location}\\n\\nThis action CANNOT be undone!\')">'
                '<i class="fas fa-trash"></i> Delete This Package Permanently</a>'
                '</div>'
            )
    package_delete_button.short_description = 'Delete Package'


# ============ PACKAGE BOOKING ADMIN ============
@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_no',
        'customer_name',
        'customer_phone',
        'package_link',
        'get_scheduled_date',
        'passengers_count',
        'total_amount',
        'advance_paid',
        'remaining_amount_display',
        'status_display',
        'payment_status_display',
        'created_at',
        'package_booking_actions_column',
    )
    
    list_filter = (
        'status', 
        'payment_status', 
        'created_at',
        'package__scheduled_date',
        'package__package_type',
        'package__vehicle_type',
    )
    
    search_fields = (
        'invoice_no', 
        'customer_name', 
        'customer_phone', 
        'customer_email',
        'package__name',
        'package__pickup_location',
        'package__drop_location',
    )
    
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = [
            'invoice_no',
            'remaining_amount_display',
            'created_at',
            'updated_at',
            'razorpay_order_id',
            'razorpay_payment_id',
            'razorpay_signature',
            'package_booking_delete_button',
            'get_scheduled_date_display',
        ]
        if obj:  # Editing existing booking
            return readonly
        return ['created_at', 'updated_at', 'package_booking_delete_button']
    
    fieldsets = (
        ('Package Information', {
            'fields': ('package', 'total_amount', 'get_scheduled_date_display')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'passengers_count'),
            'description': 'Customer contact details'
        }),
        ('Special Requirements', {
            'fields': ('special_requirements',),
            'classes': ('collapse',),
            'description': 'Any special requests from customer'
        }),
        ('Payment Information', {
            'fields': ('advance_paid', 'remaining_amount_display', 'payment_status'),
            'description': 'Payment details and status'
        }),
        ('Payment Gateway Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'),
            'classes': ('collapse',),
            'description': 'Razorpay payment gateway information'
        }),
        ('Booking Status', {
            'fields': ('status',),
            'description': 'Current booking status'
        }),
        ('Danger Zone', {
            'fields': ('package_booking_delete_button',),
            'classes': ('collapse',),
            'description': 'Package booking deletion - Use with caution'
        }),
        ('System Information', {
            'fields': ('invoice_no', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        delete_package_bookings,
        cancel_package_bookings,
        send_package_whatsapp,
    ]
    
    def get_scheduled_date(self, obj):
        if obj.package and obj.package.scheduled_date:
            return obj.package.scheduled_date
        return "Not set"
    get_scheduled_date.short_description = 'Scheduled Date'
    get_scheduled_date.admin_order_field = 'package__scheduled_date'
    
    def get_scheduled_date_display(self, obj):
        if obj.package:
            if obj.package.scheduled_date:
                time_str = ""
                if obj.package.scheduled_time:
                    time_str = f" at {obj.package.scheduled_time.strftime('%I:%M %p')}"
                return f"{obj.package.scheduled_date}{time_str}"
            return "Schedule will be confirmed by admin"
        return "No package selected"
    get_scheduled_date_display.short_description = 'Package Schedule'
    
    def package_link(self, obj):
        if obj.package:
            url = reverse('admin:packages_package_change', args=[obj.package.id])
            return format_html(f'<a href="{url}">{obj.package.name}</a>')
        return "No Package"
    package_link.short_description = 'Package'
    
    def remaining_amount_display(self, obj):
        return f"₹{obj.remaining_amount}"
    remaining_amount_display.short_description = 'Remaining'
    
    def status_display(self, obj):
        colors = {
            'PENDING': '#ffc107',  # Orange
            'CONFIRMED': '#198754',  # Green
            'COMPLETED': '#0d6efd',  # Blue
            'CANCELLED': '#dc3545',  # Red
        }
        return format_html(
            f'<span style="color:white; background-color:{colors.get(obj.status, "#6c757d")}; '
            f'padding: 3px 8px; border-radius: 3px; font-weight: bold;">'
            f'{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'
    
    def payment_status_display(self, obj):
        colors = {
            'PENDING': '#ffc107',  # Orange
            'ADVANCE_PAID': '#0d6efd',  # Blue
            'FULLY_PAID': '#198754',  # Green
        }
        return format_html(
            f'<span style="color:white; background-color:{colors.get(obj.payment_status, "#6c757d")}; '
            f'padding: 3px 8px; border-radius: 3px; font-weight: bold;">'
            f'{obj.get_payment_status_display()}</span>'
        )
    payment_status_display.short_description = 'Payment'
    
    def package_booking_actions_column(self, obj):
        """Actions column in package booking list"""
        change_url = reverse('admin:packages_packagebooking_change', args=[obj.id])
        delete_url = reverse('admin:packages_packagebooking_delete', args=[obj.id])
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            delete_button = format_html(
                f'<a href="{delete_url}" class="button" '
                'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;" '
                f'onclick="return confirm(\'Delete package booking {obj.invoice_no}?\')">'
                '<i class="fas fa-trash"></i> Delete</a>'
            )
        else:
            delete_button = format_html(
                '<span style="color:#6c757d;font-size:11px;" title="Cannot delete confirmed/completed bookings">'
                '<i class="fas fa-lock"></i> Locked</span>'
            )
        
        return format_html(
            f'<div style="display: flex; gap: 5px;">'
            f'<a href="{change_url}" class="button" style="background:#198754;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;">'
            f'<i class="fas fa-edit"></i> Edit</a>'
            f'{delete_button}'
            f'</div>'
        )
    package_booking_actions_column.short_description = 'Actions'
    
    def package_booking_delete_button(self, obj):
        """Delete button in package booking edit form"""
        if not obj.id:
            return "Save booking first to see delete option"
        
        delete_url = reverse('admin:packages_packagebooking_delete', args=[obj.id])
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            return format_html(
                '<div style="background:#f8d7da;padding:15px;border-radius:5px;border:1px solid #f5c6cb;">'
                '<h4 style="color:#721c24;margin-top:0;"><i class="fas fa-exclamation-triangle"></i> Danger Zone</h4>'
                '<p style="color:#721c24;">This action will permanently delete the package booking.</p>'
                f'<p><strong>Booking ID:</strong> {obj.invoice_no}</p>'
                f'<p><strong>Customer:</strong> {obj.customer_name}</p>'
                f'<p><strong>Package:</strong> {obj.package.name}</p>'
                f'<p><strong>Amount:</strong> ₹{obj.total_amount}</p>'
                f'<a href="{delete_url}" class="button" '
                'style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;" '
                f'onclick="return confirm(\'Are you absolutely sure?\\n\\nPackage Booking: {obj.invoice_no}\\nCustomer: {obj.customer_name}\\nPackage: {obj.package.name}\\n\\nThis action CANNOT be undone!\')">'
                '<i class="fas fa-trash"></i> Delete This Package Booking</a>'
                '</div>'
            )
        else:
            return format_html(
                '<div style="background:#fff3cd;padding:15px;border-radius:5px;border:1px solid #ffeaa7;">'
                '<h4 style="color:#856404;margin-top:0;"><i class="fas fa-lock"></i> Cannot Delete</h4>'
                f'<p style="color:#856404;">This package booking is <strong>{obj.get_status_display()}</strong>. '
                f'Only PENDING or CANCELLED package bookings can be deleted.</p>'
                f'<p>To delete this booking, first change status to CANCELLED.</p>'
                '</div>'
            )
    package_booking_delete_button.short_description = 'Delete Package Booking'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('package').order_by('-created_at')
    
    def changelist_view(self, request, extra_context=None):
        # Add custom context for change list
        extra_context = extra_context or {}
        extra_context['title'] = 'Package Bookings Management'
        extra_context['total_bookings'] = PackageBooking.objects.count()
        extra_context['confirmed_bookings'] = PackageBooking.objects.filter(status='CONFIRMED').count()
        extra_context['pending_bookings'] = PackageBooking.objects.filter(status='PENDING').count()
        return super().changelist_view(request, extra_context=extra_context)
    
    change_list_template = "admin/packages/packagebooking/change_list.html"