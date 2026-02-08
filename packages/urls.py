# packages/urls.py માં
from django.urls import path
from . import views
from .views import admin_package_bookings_pdf, admin_package_bookings_report

urlpatterns = [
    path('', views.package_list, name='package_list'),
    path('<int:package_id>/', views.package_detail, name='package_detail'),
    path('booking/<int:booking_id>/payment/', views.package_payment, name='package_payment'),
    path('payment/success/', views.package_payment_success, name='package_payment_success'),
    path('confirmation/<int:booking_id>/', views.package_booking_confirmation, name='package_booking_confirmation'),
    path('invoice/<int:booking_id>/', views.package_invoice, name='package_invoice'),
    
    # Admin reports
    path('admin/report/', admin_package_bookings_report, name='admin_package_report'),
    path('admin/report/pdf/', admin_package_bookings_pdf, name='admin_package_pdf'),
]