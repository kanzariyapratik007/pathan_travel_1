from django.contrib import admin

# Register your models here.
# gallery/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import GalleryCategory, GalleryImage, GalleryVideo

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    
    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = 'Images'


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title', 'image_type', 'category', 'is_active', 'created_at')
    list_filter = ('image_type', 'is_active', 'category')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.url}" style="width: 60px; height: 40px; object-fit: cover;" />'
            )
        return "-"
    thumbnail.short_description = 'Image'


@admin.register(GalleryVideo)
class GalleryVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'youtube_url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')