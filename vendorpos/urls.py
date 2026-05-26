from django.urls import path
from vendorpos import views

urlpatterns = [
    path("", views.panel_vendedor, name="panel_vendedor"),
    path("order/<int:order_id>/status/", views.pos_update_status, name="pos_update_status"),
]
