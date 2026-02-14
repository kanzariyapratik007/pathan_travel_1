from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, UserProfile

class CustomUserAdmin(UserAdmin):
    """Custom User Admin Panel"""
    
    list_display = (
        'id',
        'email', 
        'username', 
        'phone_display',
        'is_email_verified',
        'is_staff', 
        'is_active',
        'date_joined',
        'last_login',
        'action_buttons'
    )
    
    list_filter = (
        'is_email_verified',
        'is_phone_verified',
        'is_staff',
        'is_active',
        'is_superuser',
        'date_joined'
    )
    
    search_fields = ('email', 'username', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25
    list_editable = ('is_active', 'is_email_verified')
    date_hierarchy = 'date_joined'
    
    # Fixed readonly_fields
    readonly_fields = ('last_login', 'date_joined')
    
    fieldsets = (
        ('👤 Basic Information', {
            'fields': ('email', 'username', 'password'),
            'classes': ('wide',)
        }),
        ('📞 Contact Information', {
            'fields': ('phone', 'first_name', 'last_name'),
            'classes': ('wide',)
        }),
        ('✅ Verification Status', {
            'fields': ('is_email_verified', 'is_phone_verified', 'otp', 'otp_created_at'),
            'classes': ('collapse',)
        }),
        ('🔐 Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('📅 Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('➕ New User Registration', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone', 'password1', 'password2'),
        }),
    )
    
    def phone_display(self, obj):
        return obj.phone if obj.phone else "-"
    phone_display.short_description = 'Phone'
    
    def action_buttons(self, obj):
        return format_html(
            '<div style="display:flex; gap:5px;">'
            '<a class="button" href="/admin/users/user/{}/change/" style="background:#198754; color:white; padding:5px 10px; border-radius:3px; text-decoration:none;">'
            '<i class="fas fa-edit"></i> Edit</a>'
            '<a class="button" href="/admin/users/user/{}/delete/" style="background:#dc3545; color:white; padding:5px 10px; border-radius:3px; text-decoration:none;" '
            'onclick="return confirm(\'Are you sure you want to delete this user?\')">'
            '<i class="fas fa-trash"></i> Delete</a>'
            '</div>',
            obj.id, obj.id
        )
    action_buttons.short_description = 'Actions'
    
    actions = ['verify_emails', 'unverify_emails', 'make_active', 'make_inactive', 'export_users']
    
    def verify_emails(self, request, queryset):
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users email verified successfully.')
    verify_emails.short_description = "✅ Verify selected users email"
    
    def unverify_emails(self, request, queryset):
        updated = queryset.update(is_email_verified=False)
        self.message_user(request, f'{updated} users email unverified.')
    unverify_emails.short_description = "❌ Unverify selected users email"
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    make_active.short_description = "▶️ Make selected users active"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    make_inactive.short_description = "⏸️ Make selected users inactive"
    
    def export_users(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Email', 'Username', 'Phone', 'First Name', 'Last Name', 
                        'Email Verified', 'Active', 'Staff', 'Date Joined'])
        
        for user in queryset:
            writer.writerow([
                user.id,
                user.email,
                user.username,
                user.phone or '',
                user.first_name,
                user.last_name,
                user.is_email_verified,
                user.is_active,
                user.is_staff,
                user.date_joined.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_users.short_description = "📥 Export selected users to CSV"


class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Admin Panel"""
    
    list_display = (
        'id',
        'user_link',
        'phone_display',
        'city', 
        'state', 
        'pincode',
        'has_profile_pic',
    )
    
    list_filter = ('city', 'state')
    search_fields = ('user__email', 'user__username', 'phone', 'city', 'state')
    readonly_fields = ()
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('user',)
        }),
        ('📍 Address Information', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('🎂 Personal Information', {
            'fields': ('date_of_birth',)
        }),
        ('🖼️ Profile Picture', {
            'fields': ('profile_picture',)
        }),
        ('📞 Contact', {
            'fields': ('phone',)
        }),
    )
    
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.email
        )
    user_link.short_description = 'User'
    
    def phone_display(self, obj):
        return obj.phone if obj.phone else "-"
    phone_display.short_description = 'Phone'
    
    def has_profile_pic(self, obj):
        if obj.profile_picture:
            return format_html('✅ Yes')
        return "❌ No"
    has_profile_pic.short_description = 'Profile Pic'


# Register your models
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


# Customize Admin Site Header
admin.site.site_header = "Pathan Travels Admin Panel"
admin.site.site_title = "Pathan Travels Admin"
admin.site.index_title = "Welcome to Pathan Travels Administration"