from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('iniciar/<int:vendedor_id>/', views.iniciar_o_obtener_chat, name='iniciar_chat'),
    path('mensajes/<int:conversacion_id>/', views.obtener_mensajes, name='obtener_mensajes'),
    path('enviar/<int:conversacion_id>/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mis-chats/', views.mis_conversaciones, name='mis_conversaciones'), # 👈 NUEVA RUTA
]