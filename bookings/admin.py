# bookings/admin.py - WITH DELETE FEATURES ADDED
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from .models import Booking
import urllib.parse
import webbrowser


@admin.action(description="📱 Send WhatsApp confirmation")
def send_whatsapp_confirmation(modeladmin, request, queryset):
    for booking in queryset:
        msg = f"""Hello {booking.name} 👋

Your booking is CONFIRMED ✅

📋 Booking ID: {booking.invoice_no}
📍 Route: {booking.pickup} → {booking.drop}
📏 Distance: {booking.distance_km} KM

💰 Total Fare: ₹{booking.total_price}
💵 Advance Paid: ₹{booking.advance_paid}
💳 Remaining Amount: ₹{booking.remaining_amount}

Pathan Tours & Travels 🚗
📞 9879230065"""
        
        url = f"https://wa.me/91{booking.phone}?text={urllib.parse.quote(msg)}"
        webbrowser.open_new_tab(url)
        modeladmin.message_user(request, f"WhatsApp opened for {booking.name}")


@admin.action(description="✅ Mark as Confirmed")
def mark_as_confirmed(modeladmin, request, queryset):
    queryset.update(status='CONFIRMED')


@admin.action(description="💰 Mark as Fully Paid")
def mark_as_fully_paid(modeladmin, request, queryset):
    from django.db.models import F
    queryset.update(payment_status='FULLY_PAID', advance_paid=F('total_price'))


# ============ NEW DELETE ACTIONS ============
@admin.action(description="🗑️ Delete selected bookings")
def delete_selected_bookings(modeladmin, request, queryset):
    """કેટલીક bookings એક સાથે delete કરવી"""
    
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
    if count > 10:
        messages.warning(
            request, 
            f"You are about to delete {count} bookings. This action cannot be undone!"
        )
    
    deleted_count, _ = queryset.delete()
    messages.success(
        request, 
        f"Successfully deleted {deleted_count} booking(s)."
    )


@admin.action(description="❌ Cancel selected bookings")
def cancel_selected_bookings(modeladmin, request, queryset):
    """કેટલીક bookings cancel કરવી"""
    for booking in queryset:
        booking.status = 'CANCELLED'
        booking.payment_status = 'PENDING'
        booking.save()
    
    count = queryset.count()
    messages.success(
        request, 
        f"Successfully cancelled {count} booking(s)."
    )


@admin.action(description="🧹 Delete cancelled bookings")
def delete_cancelled_bookings(modeladmin, request, queryset):
    """Cancelled bookings delete કરવી"""
    cancelled_bookings = queryset.filter(status='CANCELLED')
    
    count = cancelled_bookings.count()
    if count == 0:
        messages.info(request, "No cancelled bookings found in selection.")
        return
    
    deleted_count, _ = cancelled_bookings.delete()
    messages.success(request, f"Deleted {deleted_count} cancelled booking(s).")


@admin.action(description="🚫 Delete pending bookings (old)")
def delete_old_pending_bookings(modeladmin, request, queryset):
    """7 દિવસથી જૂની pending bookings delete કરવી"""
    from django.utils import timezone
    from datetime import timedelta
    
    old_date = timezone.now() - timedelta(days=7)
    old_bookings = queryset.filter(
        status='PENDING',
        created_at__lt=old_date
    )
    
    count = old_bookings.count()
    if count == 0:
        messages.info(request, "No old pending bookings found.")
        return
    
    deleted_count, _ = old_bookings.delete()
    messages.success(request, f"Deleted {deleted_count} old pending booking(s).")
# ============ END NEW ACTIONS ============


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'get_invoice_no',
        'name',
        'get_phone_display',
        'get_route_display',
        'distance_km',
        'total_price',
        'advance_paid',
        'get_remaining_amount_display',
        'get_status_display',
        'get_payment_status_display',
        'created_at',
        'invoice_pdf_button',
        'delete_action_column',
    )
    
    list_filter = (
        'status',
        'payment_status',
        'created_at',
        'travel_date',
    )
    
    search_fields = (
        'invoice_no',
        'name',
        'phone',
        'email',
        'pickup',
        'drop',
    )
    
    readonly_fields = (
        'get_invoice_no_display',
        'get_created_at_display',
        'get_updated_at_display',
        'get_remaining_amount_display_admin',
        'razorpay_order_id',
        'razorpay_payment_id',
        'razorpay_signature',
        'delete_button_field',  # NEW FIELD
    )
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('get_invoice_no_display', 'get_created_at_display', 'get_updated_at_display')
        }),
        ('Customer Details', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Trip Details', {
            'fields': ('pickup', 'drop', 'distance_km', 'travel_date', 'travel_time')
        }),
        ('Payment Information', {
            'fields': ('total_price', 'advance_paid', 'get_remaining_amount_display_admin')
        }),
        ('Payment Gateway', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('System Actions', {
            'fields': ('delete_button_field',),
            'classes': ('collapse',),
            'description': 'Danger Zone - Use with caution'
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    # ============ UPDATED ACTIONS LIST ============
    actions = [
        send_whatsapp_confirmation, 
        mark_as_confirmed, 
        mark_as_fully_paid,
        cancel_selected_bookings,          # NEW
        delete_selected_bookings,          # NEW
        delete_cancelled_bookings,         # NEW
        delete_old_pending_bookings,       # NEW
    ]
    # ============ END ACTIONS UPDATE ============
    
    # Custom methods for list_display
    def get_invoice_no(self, obj):
        return obj.invoice_no or "N/A"
    get_invoice_no.short_description = 'Invoice No'
    
    def get_phone_display(self, obj):
        return format_html(f'<a href="tel:{obj.phone}">{obj.phone}</a>')
    get_phone_display.short_description = 'Phone'
    
    def get_route_display(self, obj):
        return f"{obj.pickup} → {obj.drop}"
    get_route_display.short_description = 'Route'
    
    def get_remaining_amount_display(self, obj):
        return f"₹{obj.remaining_amount}"
    get_remaining_amount_display.short_description = 'Remaining'
    
    def get_status_display(self, obj):
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
    get_status_display.short_description = 'Status'
    
    def get_payment_status_display(self, obj):
        colors = {
            'PENDING': 'orange',
            'ADVANCE_PAID': 'blue',
            'FULLY_PAID': 'green',
        }
        return format_html(
            f'<span style="color:{colors.get(obj.payment_status, "black")}; font-weight:bold;">'
            f'{obj.get_payment_status_display()}</span>'
        )
    get_payment_status_display.short_description = 'Payment'
    
    def invoice_pdf_button(self, obj):
        if not obj.id:
            return "-"
        
        pdf_url = reverse('admin_booking_invoice', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" class="button" '
            'style="background:#0d6efd;color:white;padding:3px 8px;'
            'border-radius:3px;text-decoration:none;font-size:11px;">'
            '<i class="fas fa-file-pdf"></i> PDF</a>',
            pdf_url
        )
    invoice_pdf_button.short_description = "Invoice"
    
    # ============ NEW METHOD FOR DELETE COLUMN ============
    def delete_action_column(self, obj):
        """Delete actions column in list view"""
        delete_url = reverse('admin:bookings_booking_delete', args=[obj.id])
        change_url = reverse('admin:bookings_booking_change', args=[obj.id])
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            delete_button = format_html(
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;" '
                f'onclick="return confirm(\'Delete booking {obj.invoice_no}?\')">'
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
    delete_action_column.short_description = 'Actions'
    # ============ END NEW METHOD ============
    
    # Custom methods for readonly_fields
    def get_invoice_no_display(self, obj):
        return obj.invoice_no or "Will be generated on save"
    get_invoice_no_display.short_description = 'Invoice No'
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    get_created_at_display.short_description = 'Created At'
    
    def get_updated_at_display(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    get_updated_at_display.short_description = 'Updated At'
    
    def get_remaining_amount_display_admin(self, obj):
        color = 'green' if obj.remaining_amount == 0 else 'orange' if obj.remaining_amount < obj.total_price else 'red'
        return format_html(f'<span style="color:{color}; font-weight:bold;">₹{obj.remaining_amount}</span>')
    get_remaining_amount_display_admin.short_description = 'Remaining Amount'
    
    # ============ NEW METHOD FOR DELETE BUTTON IN FORM ============
    def delete_button_field(self, obj):
        """Delete button in booking edit form"""
        if not obj.id:
            return "Save booking first to see delete option"
        
        delete_url = reverse('admin:bookings_booking_delete', args=[obj.id])
        
        # Check if booking can be deleted
        can_delete = obj.status not in ['CONFIRMED', 'COMPLETED']
        
        if can_delete:
            return format_html(
                f'<div style="background:#f8d7da;padding:15px;border-radius:5px;border:1px solid #f5c6cb;">'
                f'<h4 style="color:#721c24;margin-top:0;"><i class="fas fa-exclamation-triangle"></i> Danger Zone</h4>'
                f'<p style="color:#721c24;">This action will permanently delete the booking.</p>'
                f'<a href="{delete_url}" class="button" '
                f'style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;" '
                f'onclick="return confirm(\'Are you absolutely sure?\\n\\nBooking: {obj.invoice_no}\\nCustomer: {obj.name}\\nRoute: {obj.pickup} → {obj.drop}\\n\\nThis action CANNOT be undone!\')">'
                f'<i class="fas fa-trash"></i> Delete This Booking Permanently</a>'
                f'</div>'
            )
        else:
            return format_html(
                f'<div style="background:#fff3cd;padding:15px;border-radius:5px;border:1px solid #ffeaa7;">'
                f'<h4 style="color:#856404;margin-top:0;"><i class="fas fa-lock"></i> Cannot Delete</h4>'
                f'<p style="color:#856404;">This booking is <strong>{obj.get_status_display()}</strong>. '
                f'Only PENDING or CANCELLED bookings can be deleted.</p>'
                f'<p>To delete this booking, first change status to CANCELLED.</p>'
                f'</div>'
            )
    delete_button_field.short_description = 'Delete Booking'
    
    # ============ OVERRIDE DEFAULT DELETE VIEW ============
    def get_actions(self, request):
        """કસ્ટમ actions"""
        actions = super().get_actions(request)
        
        # Add confirmation for delete action
        if 'delete_selected_bookings' in actions:
            actions['delete_selected_bookings'] = (
                delete_selected_bookings,
                'delete_selected_bookings',
                "🗑️ Delete selected bookings (confirmation will appear)"
            )
        
        return actions
    
    def delete_view(self, request, object_id, extra_context=None):
        """કસ્ટમ delete view"""
        from django.shortcuts import get_object_or_404
        from django.template.response import TemplateResponse
        
        booking = get_object_or_404(Booking, id=object_id)
        
        # Check if booking can be deleted
        if booking.status in ['CONFIRMED', 'COMPLETED']:
            messages.error(
                request, 
                f"Cannot delete {booking.get_status_display().lower()} booking. "
                f"Please cancel it first."
            )
            return self.change_view(request, object_id)
        
        extra_context = extra_context or {}
        extra_context.update({
            'booking': booking,
            'can_delete': booking.status not in ['CONFIRMED', 'COMPLETED'],
        })
        
        return super().delete_view(request, object_id, extra_context)