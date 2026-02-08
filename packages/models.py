from django.db import models

# Create your models here.
from django.db import models

class TravelPackage(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_km = models.IntegerField(default=14)
    festival_price = models.IntegerField(default=16)

    def __str__(self):
        return self.title
# packages/models.py
# packages/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Package(models.Model):
    PACKAGE_TYPES = [
        ('HONEYMOON', 'Honeymoon'),
        ('FAMILY', 'Family'),
        ('ADVENTURE', 'Adventure'),
        ('PILGRIMAGE', 'Pilgrimage'),
        ('CUSTOM', 'Custom'),
    ]
    
    VEHICLE_TYPES = [
        ('SEDAN', 'Sedan (4-Seater)'),
        ('SUV', 'SUV (6-7 Seater)'),
        ('TEMPO', 'Tempo Traveler (12 Seater)'),
        ('BUS', 'Mini Bus (20-25 Seater)'),
    ]
    
    # Package Details
    name = models.CharField(max_length=200)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    description = models.TextField()
    
    # Route Details
    pickup_location = models.CharField(max_length=200)
    drop_location = models.CharField(max_length=200)
    distance_km = models.FloatField(validators=[MinValueValidator(0)])
    
    # Package Details
    duration_days = models.IntegerField(default=1)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    max_passengers = models.IntegerField(default=4)
    
    # Pricing
    base_price = models.IntegerField()
    advance_amount = models.IntegerField(default=1000)
    is_festival_rate = models.BooleanField(default=False)
    
    # Images
    cover_image = models.ImageField(upload_to='packages/', blank=True, null=True)
    # gallery_images field removed for now
    
    # Inclusions
    inclusions = models.TextField(help_text="Separate with comma")
    exclusions = models.TextField(help_text="Separate with comma")
    
    # Important Notes
    important_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.pickup_location} to {self.drop_location})"
    
    @property
    def final_price(self):
        if self.is_festival_rate:
            return int(self.base_price * 1.15)
        return self.base_price
    
    @property
    def remaining_amount(self):
        return self.final_price - self.advance_amount
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'


class PackageBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ADVANCE_PAID', 'Advance Paid'),
        ('FULLY_PAID', 'Fully Paid'),
    ]
    
    # Package Reference
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='bookings')
    
    # Customer Information
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=10)
    customer_email = models.EmailField(blank=True, null=True)
    passengers_count = models.IntegerField(default=1)
    
    # Travel Details
    travel_date = models.DateField()
    travel_time = models.TimeField()
    
    # Special Requirements
    special_requirements = models.TextField(blank=True)
    
    # Payment Details
    total_amount = models.IntegerField()
    advance_paid = models.IntegerField(default=1000)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Invoice
    invoice_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_no:
            date_str = timezone.now().strftime("%Y%m%d")
            last_booking = PackageBooking.objects.filter(
                invoice_no__contains=f"PTP-{date_str}"
            ).order_by('-id').first()
            
            if last_booking and last_booking.invoice_no:
                try:
                    last_num = int(last_booking.invoice_no.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.invoice_no = f"PTP-{date_str}-{new_num:04d}"
        
        if self.package and not self.total_amount:
            self.total_amount = self.package.final_price
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_amount(self):
        return self.total_amount - self.advance_paid
    
    def __str__(self):
        return f"{self.invoice_no} - {self.customer_name} - {self.package.name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Package Booking'
        verbose_name_plural = 'Package Bookings'