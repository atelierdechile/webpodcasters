from django.urls import path
from . import views
from .views import preferences_kpis


app_name = 'analytics' 

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('manychat/', views.manychat_log, name='analytics_manychat'),
    path('graficos/', views.graficos, name='graficos'),
    path('api/data/', views.analytics_data, name='analytics_data'),
    path('api/horas/', views.analytics_horas, name='analytics_horas'),
    path("preferences_kpis/", preferences_kpis, name="preferences_kpis"),
    path("admin/sales-data/", views.admin_sales_data, name="admin_sales_data"),
    path("admin/top-products/", views.admin_top_products, name="admin_top_products"),

    # 🚀 RUTAS JSON DEL DASHBOARD DEL VENDEDOR
    path("vendor/sales-data/", views.vendor_sales_data, name="vendor_sales_data"),
    path("vendor/top-products/", views.vendor_top_products, name="vendor_top_products"),


    
    path("api/map/vendors-sales-today/", views.map_vendors_sales_today, name="map_vendors_sales_today"),
    path( "api/map/vendors-sales-total/",views.map_vendors_sales_total,name="map_vendors_sales_total"),


]

