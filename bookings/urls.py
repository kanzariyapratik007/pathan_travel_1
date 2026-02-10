from django.urls import path
from . import views
from .views import admin_delete_booking 

urlpatterns = [
    path('', views.book_trip, name='book_trip'),
    path('payment/<int:booking_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('invoice/<int:booking_id>/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('contact/', views.contact, name='contact'),
    path('simulate/<int:booking_id>/', views.simulate_payment_direct, name='simulate_payment'),
    path('admin/delete/<int:booking_id>/', admin_delete_booking, name='admin_delete_booking'),
    path('admin/bookings/<int:booking_id>/invoice/',views.generate_invoice_pdf,name='admin_booking_invoice'),
    
]