from django.urls import path
from . import views

app_name = "superadmin_panel"

urlpatterns = [
    # =========================
    # VENDEDORES / CREADORES
    # =========================
    path("vendedores/", views.vendor_list, name="vendor_list"),
    path("vendedores/<int:vendor_id>/productos/", views.vendor_products, name="vendor_products"),       
    path("vendors/<int:vendor_id>/edit/", views.vendor_edit, name="vendor_edit"),
    path("vendors/<int:vendor_id>/delete/", views.vendor_delete, name="vendor_delete"),

    # =========================
    # PRODUCTOS / SERVICIOS
    # =========================
    path("productos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path("productos/<int:pk>/eliminar/", views.product_delete, name="product_delete"),

    # =========================
    # OFERTAS / DESCUENTOS
    # =========================
    path("ofertas/", views.offer_list, name="offer_list"),
    path("ofertas/nueva/", views.offer_edit, name="offer_create"),
    path("ofertas/<int:pk>/editar/", views.offer_edit, name="offer_edit"),
    path("ofertas/<int:pk>/eliminar/", views.offer_delete, name="offer_delete"),

    # =========================
    # MENSAJERÍA MASIVA / REGIONAL
    # =========================
    path("vendor/", views.vendor_messaging, name="vendor_messaging"),
    path("vendor/history/", views.vendor_messaging_history, name="vendor_messaging_history"),

    # API de dependencias geográficas (Chile)
    path("api/provincias/", views.api_provincias, name="api_provincias"),
    path("api/comunas/", views.api_comunas, name="api_comunas"),

    # =========================
    # COMPRADORES / USUARIOS
    # =========================
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:customer_id>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/<int:customer_id>/delete/", views.customer_delete, name="customer_delete"),
]