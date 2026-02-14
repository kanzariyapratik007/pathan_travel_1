# pathan_travels/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import home, contact  # 'contact_view' નહીં, 'contact'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', home, name='home'),
    path('contact/', contact, name='contact'),  # name='contact' છે
    path('', include('users.urls')),
    path('book/', include('bookings.urls')),
    path('packages/', include('packages.urls')),
    path('gallery/', include('gallery.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

