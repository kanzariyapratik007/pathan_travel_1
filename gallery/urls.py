# gallery/urls.py
from django.urls import path
from . import views

# gallery/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('images/', views.images_view, name='gallery_images'),
    path('videos/', views.videos_view, name='gallery_videos'),
]