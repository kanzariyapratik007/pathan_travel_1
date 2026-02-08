from django.shortcuts import render

# Create your views here.
# gallery/views.py
from django.shortcuts import render

# pathan_travels/views.py (or wherever your views are)
from django.shortcuts import render

def gallery(request):
    # Your gallery logic here
    # For example, fetch images from database
    context = {
        'title': 'Photo Gallery',
        # Add your context data here
    }
    return render(request, 'gallery.html', context)

# gallery/views.py
from django.shortcuts import render
from .models import GalleryImage, GalleryVideo, GalleryCategory

def gallery_view(request):
    images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')[:12]
    videos = GalleryVideo.objects.filter(is_active=True).order_by('-created_at')[:6]
    categories = GalleryCategory.objects.filter(is_active=True)
    
    context = {
        'images': images,
        'videos': videos,
        'categories': categories,
    }
    return render(request, 'gallery/gallery.html', context)

def images_view(request):
    category_id = request.GET.get('category', None)
    
    if category_id:
        images = GalleryImage.objects.filter(
            is_active=True, 
            category_id=category_id
        ).order_by('-created_at')
    else:
        images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')
    
    categories = GalleryCategory.objects.filter(is_active=True)
    
    context = {
        'images': images,
        'categories': categories,
        'selected_category': category_id,
    }
    return render(request, 'gallery/images.html', context)

def videos_view(request):
    videos = GalleryVideo.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'gallery/videos.html', {'videos': videos})