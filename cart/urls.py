from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart'),
    path('success/', views.success, name='success'),
    path('failure/', views.failure, name='failure'),
    path('pending/', views.pending, name='pending'),
    path('checkout/start/', views.checkout_start, name='checkout_start'),
    path('webhook/', views.webhook, name='webhook'),
]

