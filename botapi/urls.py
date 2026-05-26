from django.urls import path
from . import views
from .views import check_user

urlpatterns = [
    #  Carrito temporal
    path("cart/create/", views.create_cart, name="create_cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("view_cart/", views.view_cart, name="view_cart"), 

    # Verificación de usuario
    path("check_user/", check_user, name="check_user"),

    # Productos
    path("pizzas_cards/", views.pizzas_cards, name="pizzas_cards"),
    # path("pizzas_list/", views.pizzas_list, name="pizzas_list"),
    # path("pizza_detail/", views.pizza_detail, name="pizza_detail"),

    # Nueva ruta para pagar pedido
    path("pay_order/", views.pay_order, name="pay_order"),
    # autologin
    path("auto-login/<str:token>/", views.auto_login, name="auto_login"),
]
