"""
Django settings for pathan_travels project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-12345')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom Apps
    'core',
    'packages',
    'bookings',
    'gallery',
    'users',
]
AUTH_USER_MODEL = 'users.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pathan_travels.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pathan_travels.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'kanzariyapratik124@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_e664V0FP0zQy7N')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'QdnuRxUHrPGeiJc9lDTXYPO7')

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC820e3c0f356f546f11410d7e04297390')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'c26066605db3ecbf0fde51b0a6d07cd7')
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Contact Information
CONTACT_EMAIL = 'kanzariyapratik124@gmail.com'
CONTACT_PHONES = ['9879230065', '9925993770']
SITE_URL = 'http://127.0.0.1:8000'

# Security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# settings.py માં આ ઉમેરો:
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'    

# settings.py માં આ ઉમેરો:
RAZORPAY_KEY_ID = 'rzp_test_e664V0FP0zQy7N'  # તમારી key
RAZORPAY_KEY_SECRET = 'QdnuRxUHrPGeiJc9lDTXYPO7'  # તમારી secret


# Jazzmin Settings for better admin UI
JAZZMIN_SETTINGS = {
    "site_title": "Pathan Travels Admin",
    "site_header": "Pathan Travels",
    "site_brand": "Pathan Travels",
    "site_logo": None,
    "welcome_sign": "Welcome to Pathan Travels Admin Panel",
    "copyright": "Pathan Travels",
    "search_model": ["users.User", "bookings.Booking"],
    
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    
    "usermenu_links": [
        {"name": "Profile", "url": "admin:users_user_changelist"},
    ],
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        "users.User": "fas fa-user",
        "users.UserProfile": "fas fa-id-card",
        "bookings.Booking": "fas fa-ticket-alt",
        "packages.Package": "fas fa-box",
        "packages.PackageBooking": "fas fa-shopping-cart",
        "gallery.GalleryImage": "fas fa-image",
        "gallery.GalleryVideo": "fas fa-video",
        "auth.Group": "fas fa-users-cog",
    },
    
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    "related_modal_active": True,
    
    "custom_links": {
        "users": [{
            "name": "User Statistics", 
            "url": "admin:users_user_changelist", 
            "icon": "fas fa-chart-bar",
        }]
    },
    
    "show_ui_builder": True,
    
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.User": "collapsible",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-success",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}