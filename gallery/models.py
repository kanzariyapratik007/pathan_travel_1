from django.db import models

# Create your models here.
# gallery/models.py
from django.db import models
from django.utils import timezone

class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Gallery Categories"
        ordering = ['name']


class GalleryImage(models.Model):
    IMAGE_TYPES = [
        ('VEHICLE', 'Vehicle'),
        ('DESTINATION', 'Destination'),
        ('TRIP', 'Trip'),
        ('CUSTOMER', 'Customer'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES, default='TRIP')
    category = models.ForeignKey(GalleryCategory, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='images')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class GalleryVideo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    youtube_url = models.URLField()
    thumbnail = models.ImageField(upload_to='gallery/videos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']