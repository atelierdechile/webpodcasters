# superadmin_panel/urls.py

from django.urls import path
from . import views

app_name = "superadmin_panel"

urlpatterns = [
    # Vendedores
    path("vendedores/", views.vendor_list, name="vendor_list"),
    path("vendedores/<int:vendor_id>/productos/", views.vendor_products, name="vendor_products"),       
    path("vendors/<int:vendor_id>/edit/", views.vendor_edit, name="vendor_edit"),
    path("vendors/<int:vendor_id>/delete/", views.vendor_delete, name="vendor_delete"),

    # Productos
    path("productos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path("productos/<int:pk>/eliminar/", views.product_delete, name="product_delete"),

    # Ofertas
    path("ofertas/", views.offer_list, name="offer_list"),
    path("ofertas/nueva/", views.offer_edit, name="offer_create"),
    path("ofertas/<int:pk>/editar/", views.offer_edit, name="offer_edit"),
    path("ofertas/<int:pk>/eliminar/", views.offer_delete, name="offer_delete"),

    # Menú semanal (listado tipo tabla)
    path("menu-semanal/", views.weekly_menu_list, name="weekly_menu_list"),

    # 👉 Editor visual de menú semanal (el que replica la vista del vendedor)
    path("menu-semanal/nuevo/", views.weekly_menu_admin, name="weekly_menu_create"),

    # Edición / borrado de un registro puntual (si quieres mantener la vista simple por formulario)
    path("menu-semanal/<int:pk>/editar/", views.weekly_menu_edit, name="weekly_menu_edit"),
    path("menu-semanal/<int:pk>/eliminar/", views.weekly_menu_delete, name="weekly_menu_delete"),

    # Ingredientes
    path("ingredientes/", views.ingredient_list, name="ingredient_list"),
    path("ingredientes/nuevo/", views.ingredient_edit, name="ingredient_create"),
    path("ingredientes/<int:pk>/editar/", views.ingredient_edit, name="ingredient_edit"),
    path("ingredientes/<int:pk>/eliminar/", views.ingredient_delete, name="ingredient_delete"),

    # Categorías de ingredientes
    path("ingredientes/categorias/", views.ingredient_category_list, name="ingredient_category_list"),
    path("ingredientes/categorias/nueva/", views.ingredient_category_edit, name="ingredient_category_create"),
    path("ingredientes/categorias/<int:pk>/editar/", views.ingredient_category_edit, name="ingredient_category_edit"),
    path("ingredientes/categorias/<int:pk>/eliminar/", views.ingredient_category_delete, name="ingredient_category_delete"),

    # API para drag & drop del súper admin
    path("menu-semanal/api/asignar/", views.weekly_menu_assign_admin, name="weekly_menu_assign_admin"),
    path("menu-semanal/api/clear/", views.weekly_menu_clear_admin, name="weekly_menu_clear_admin"),


    path("ingredients/manage/", views.ingredient_manage, name="ingredient_manage"),



    path("vendor/", views.vendor_messaging, name="vendor_messaging"),
    path("vendor/history/", views.vendor_messaging_history, name="vendor_messaging_history"),

    path("api/provincias/", views.api_provincias, name="api_provincias"),
    path("api/comunas/", views.api_comunas, name="api_comunas"),

    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:customer_id>/edit/",views.customer_edit, name="customer_edit"),
    path("customers/<int:customer_id>/delete/",views.customer_delete,name="customer_delete",),
]
