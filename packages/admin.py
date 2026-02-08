# packages/admin.py - FIXED VERSION
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Package, PackageBooking


# ============ PACKAGE BOOKING DELETE ACTIONS ============
@admin.action(description="🗑️ Delete selected package bookings")
def delete_package_bookings(modeladmin, request, queryset):
    """કેટલીક package bookings એક સાથે delete કરવી"""
    
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
    """કેટલીક package bookings cancel કરવી"""
    for booking in queryset:
        booking.status = 'CANCELLED'
        booking.payment_status = 'PENDING'
        booking.save()
    
    count = queryset.count()
    messages.success(
        request, 
        f"Successfully cancelled {count} package booking(s)."
    )


@admin.action(description="📱 Send WhatsApp for packages")
def send_package_whatsapp(modeladmin, request, queryset):
    """Package bookings માટે WhatsApp મેસેજ"""
    import urllib.parse
    
    for booking in queryset:
        package = booking.package
        site_url = "http://127.0.0.1:8000"
        
        msg = f"""Hello {booking.customer_name} 👋

✨ **Package Booking Confirmed!** ✨

📦 Package: {package.name}
📋 Booking ID: {booking.invoice_no}
📍 Route: {package.pickup_location} → {package.drop_location}
📏 Distance: {package.distance_km} KM
⏳ Duration: {package.duration_days} Day(s)
🚗 Vehicle: {package.get_vehicle_type_display()}
👥 Passengers: {booking.passengers_count}
🗓 Travel Date: {booking.travel_date}
⏰ Travel Time: {booking.travel_time.strftime('%I:%M %p')}

💰 Total Fare: ₹{booking.total_amount}
💵 Advance Paid: ₹{booking.advance_paid}
💳 Remaining: ₹{booking.remaining_amount}

Thank you for choosing Pathan Travels! 🚗"""
        
        whatsapp_url = f"https://wa.me/91{booking.customer_phone}?text={urllib.parse.quote(msg)}"
        
        messages.info(
            request, 
            f"WhatsApp for {booking.customer_name}: "
            f"<a href='{whatsapp_url}' target='_blank'>Click here</a>"
        )
# ============ END DELETE ACTIONS ============


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'package_type',
        'route_display',
        'distance_km',
        'duration_days',
        'vehicle_type',
        'base_price',
        'final_price',
        'is_active',
        'created_at',
        'package_actions_column',  # NEW COLUMN
    )
    
    list_filter = ('package_type', 'vehicle_type', 'is_active', 'is_festival_rate')
    search_fields = ('name', 'pickup_location', 'drop_location', 'description')
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'final_price_display',
        'package_delete_button',  # NEW FIELD
    )
    
    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'package_type', 'description', 'is_active')
        }),
        ('Route Details', {
            'fields': ('pickup_location', 'drop_location', 'distance_km', 'duration_days')
        }),
        ('Vehicle Details', {
            'fields': ('vehicle_type', 'max_passengers')
        }),
        ('Pricing', {
            'fields': ('base_price', 'advance_amount', 'is_festival_rate', 'final_price_display')
        }),
        ('Inclusions & Exclusions', {
            'fields': ('inclusions', 'exclusions'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('cover_image',),
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
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def route_display(self, obj):
        return f"{obj.pickup_location} → {obj.drop_location}"
    route_display.short_description = 'Route'
    
    def final_price(self, obj):
        if obj.is_festival_rate:
            return f"₹{int(obj.base_price * 1.15)} (Festival)"
        return f"₹{obj.base_price}"
    final_price.short_description = 'Final Price'
    
    def final_price_display(self, obj):
        return self.final_price(obj)
    final_price_display.short_description = 'Final Price'
    
    # ============ FIXED: PACKAGE DELETE FEATURES ============
    def package_actions_column(self, obj):
        """Package list માં actions column"""
        # Hardcoded URLs વાપરો
        change_url = f"/admin/packages/package/{obj.id}/change/"
        delete_url = f"/admin/packages/package/{obj.id}/delete/"
        
        # Check if package has any bookings
        has_bookings = obj.bookings.exists()
        
        if has_bookings:
            delete_button = format_html(
                f'<span style="color:#6c757d;font-size:11px;" title="Cannot delete - Has bookings">'
                f'<i class="fas fa-lock"></i> Locked</span>'
            )
        else:
            delete_button = format_html(
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;" '
                f'onclick="return confirm(\'Delete package {obj.name}?\')">'
                f'<i class="fas fa-trash"></i> Delete</a>'
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
        """Package edit form માં delete button"""
        if not obj.id:
            return "Save package first to see delete option"
        
        delete_url = f"/admin/packages/package/{obj.id}/delete/"
        
        # Check if package has bookings
        has_bookings = obj.bookings.exists()
        
        if has_bookings:
            booking_count = obj.bookings.count()
            return format_html(
                f'<div style="background:#fff3cd;padding:15px;border-radius:5px;border:1px solid #ffeaa7;">'
                f'<h4 style="color:#856404;margin-top:0;"><i class="fas fa-lock"></i> Cannot Delete Package</h4>'
                f'<p style="color:#856404;">This package has <strong>{booking_count} booking(s)</strong>. '
                f'You must delete all bookings first before deleting the package.</p>'
                f'<p><a href="../packagebooking/?package__id__exact={obj.id}" style="color:#198754;">'
                f'<i class="fas fa-external-link-alt"></i> View Package Bookings</a></p>'
                f'</div>'
            )
        else:
            return format_html(
                f'<div style="background:#f8d7da;padding:15px;border-radius:5px;border:1px solid #f5c6cb;">'
                f'<h4 style="color:#721c24;margin-top:0;"><i class="fas fa-exclamation-triangle"></i> Danger Zone</h4>'
                f'<p style="color:#721c24;">This action will permanently delete the package.</p>'
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;" '
                f'onclick="return confirm(\'Are you absolutely sure?\\n\\nPackage: {obj.name}\\nRoute: {obj.pickup_location} → {obj.drop_location}\\n\\nThis action CANNOT be undone!\')">'
                f'<i class="fas fa-trash"></i> Delete This Package Permanently</a>'
                f'</div>'
            )
    package_delete_button.short_description = 'Delete Package'
    # ============ END PACKAGE DELETE FEATURES ============


@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_no',
        'customer_name',
        'customer_phone',
        'package_link',
        'travel_date',
        'passengers_count',
        'total_amount',
        'advance_paid',
        'remaining_amount_display',
        'status_display',
        'payment_status_display',
        'created_at',
        'package_booking_actions_column',  # NEW COLUMN
    )
    
    list_filter = ('status', 'payment_status', 'created_at', 'travel_date')
    search_fields = ('invoice_no', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = (
        'invoice_no',
        'remaining_amount_display',
        'created_at',
        'updated_at',
        'razorpay_order_id',
        'razorpay_payment_id',
        'razorpay_signature',
        'package_booking_delete_button',  # NEW FIELD
    )
    
    fieldsets = (
        ('Package Information', {
            'fields': ('package', 'total_amount')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'passengers_count')
        }),
        ('Travel Details', {
            'fields': ('travel_date', 'travel_time', 'special_requirements')
        }),
        ('Payment Information', {
            'fields': ('advance_paid', 'remaining_amount_display', 'payment_status')
        }),
        ('Payment Gateway', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Danger Zone', {
            'fields': ('package_booking_delete_button',),
            'classes': ('collapse',),
            'description': 'Package booking deletion'
        }),
        ('System', {
            'fields': ('invoice_no', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # ============ UPDATED ACTIONS FOR PACKAGE BOOKINGS ============
    actions = [
        delete_package_bookings,  # NEW
        cancel_package_bookings,  # NEW
        send_package_whatsapp,    # NEW
    ]
    
    def package_link(self, obj):
        return obj.package.name
    package_link.short_description = 'Package'
    
    def remaining_amount_display(self, obj):
        return f"₹{obj.remaining_amount}"
    remaining_amount_display.short_description = 'Remaining'
    
    def status_display(self, obj):
        colors = {
            'PENDING': 'orange',
            'CONFIRMED': 'green',
            'COMPLETED': 'blue',
            'CANCELLED': 'red',
        }
        return format_html(
            f'<span style="color:{colors.get(obj.status, "black")}; font-weight:bold;">'
            f'{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'
    
    def payment_status_display(self, obj):
        colors = {
            'PENDING': 'orange',
            'ADVANCE_PAID': 'blue',
            'FULLY_PAID': 'green',
        }
        return format_html(
            f'<span style="color:{colors.get(obj.payment_status, "black")}; font-weight:bold;">'
            f'{obj.get_payment_status_display()}</span>'
        )
    payment_status_display.short_description = 'Payment'
    
    # ============ FIXED: PACKAGE BOOKING DELETE FEATURES ============
    def package_booking_actions_column(self, obj):
        """Package booking list માં actions column"""
        # Hardcoded URLs વાપરો
        change_url = f"/admin/packages/packagebooking/{obj.id}/change/"
        delete_url = f"/admin/packages/packagebooking/{obj.id}/delete/"
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            delete_button = format_html(
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;" '
                f'onclick="return confirm(\'Delete package booking {obj.invoice_no}?\')">'
                f'<i class="fas fa-trash"></i> Delete</a>'
            )
        else:
            delete_button = format_html(
                f'<span style="color:#6c757d;font-size:11px;">'
                f'<i class="fas fa-lock"></i> Locked</span>'
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
        """Package booking edit form માં delete button"""
        if not obj.id:
            return "Save booking first to see delete option"
        
        delete_url = f"/admin/packages/packagebooking/{obj.id}/delete/"
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            return format_html(
                f'<div style="background:#f8d7da;padding:15px;border-radius:5px;border:1px solid #f5c6cb;">'
                f'<h4 style="color:#721c24;margin-top:0;"><i class="fas fa-exclamation-triangle"></i> Danger Zone</h4>'
                f'<p style="color:#721c24;">This action will permanently delete the package booking.</p>'
                f'<p><strong>Booking:</strong> {obj.invoice_no}</p>'
                f'<p><strong>Customer:</strong> {obj.customer_name}</p>'
                f'<p><strong>Package:</strong> {obj.package.name}</p>'
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;" '
                f'onclick="return confirm(\'Are you absolutely sure?\\n\\nPackage Booking: {obj.invoice_no}\\nCustomer: {obj.customer_name}\\nPackage: {obj.package.name}\\n\\nThis action CANNOT be undone!\')">'
                f'<i class="fas fa-trash"></i> Delete This Package Booking</a>'
                f'</div>'
            )
        else:
            return format_html(
                f'<div style="background:#fff3cd;padding:15px;border-radius:5px;border:1px solid #ffeaa7;">'
                f'<h4 style="color:#856404;margin-top:0;"><i class="fas fa-lock"></i> Cannot Delete</h4>'
                f'<p style="color:#856404;">This package booking is <strong>{obj.get_status_display()}</strong>. '
                f'Only PENDING or CANCELLED package bookings can be deleted.</p>'
                f'<p>To delete this booking, first change status to CANCELLED.</p>'
                f'</div>'
            )
    package_booking_delete_button.short_description = 'Delete Package Booking'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('package')
    
    change_list_template = "admin/packages/packagebooking/change_list.html"