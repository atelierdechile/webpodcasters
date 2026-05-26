from django.urls import path
from vendorapi import views

urlpatterns = [
    path("orders/", views.vendor_orders),
    path("orders/<int:order_id>/", views.vendor_order_detail),
    path("orders/<int:order_id>/status/", views.vendor_update_status),
]


