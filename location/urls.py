from django.urls import path
from . import views

urlpatterns = [
    path('ajax/cargar-provincias/', views.cargar_provincias, name='ajax_cargar_provincias'),
    path('ajax/cargar-comunas/', views.cargar_comunas, name='ajax_cargar_comunas'),
]

