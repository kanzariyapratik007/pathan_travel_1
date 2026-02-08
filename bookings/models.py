# bookings/models.py
from django.db import models
from django.utils import timezone

class Booking(models.Model):
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
    
    # Basic Information
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)
    
    # Trip Details
    pickup = models.CharField(max_length=200)
    drop = models.CharField(max_length=200)
    distance_km = models.FloatField()
    
    # Date and Time
    travel_date = models.DateField()
    travel_time = models.TimeField()
    
    # Pricing
    total_price = models.IntegerField()
    advance_paid = models.IntegerField(default=1000)
    
    # Payment Information
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
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_no:
            date_str = timezone.now().strftime("%Y%m%d")
            prefix = f"PT-{date_str}-"
            
            # Find the last invoice number for today
            last_invoice = Booking.objects.filter(
                invoice_no__startswith=prefix
            ).order_by('-invoice_no').first()
            
            if last_invoice and last_invoice.invoice_no:
                try:
                    last_num = int(last_invoice.invoice_no.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.invoice_no = f"{prefix}{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_amount(self):
        return self.total_price - self.advance_paid
    
    def __str__(self):
        return f"{self.invoice_no} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'