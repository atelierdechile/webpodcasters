from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .models import Conversacion, Mensaje

User = get_user_model()

@login_required
def iniciar_o_obtener_chat(request, vendedor_id):
    """Busca si ya existe un chat entre el comprador logueado y el vendedor, o crea uno nuevo."""
    vendedor = get_object_or_404(User, id=vendedor_id)
    
    if request.user == vendedor:
        return JsonResponse({'error': 'No puedes chatear contigo mismo'}, status=400)

    conversacion, created = Conversacion.objects.get_or_create(
        comprador=request.user,
        vendedor=vendedor
    )
    return JsonResponse({'conversacion_id': conversacion.id})

@login_required
def obtener_mensajes(request, conversacion_id):
    """Devuelve la lista de mensajes en formato JSON."""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    # Seguridad: Solo el comprador o el vendedor pueden ver el chat
    if request.user != conversacion.comprador and request.user != conversacion.vendedor:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    mensajes = conversacion.mensajes.all()
    data = [
        {
            'id': m.id,
            'emisor': m.emisor.username,
            'es_mío': m.emisor == request.user,
            'texto': m.texto,
            'hora': m.fecha_envio.strftime('%H:%M')
        }
        for m in mensajes
    ]
    return JsonResponse({'mensajes': data})

@login_required
@require_POST
def enviar_mensaje(request, conversacion_id):
    """Guarda un nuevo mensaje recibido por AJAX."""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    if request.user != conversacion.comprador and request.user != conversacion.vendedor:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    texto = request.POST.get('texto', '').strip()
    if texto:
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            emisor=request.user,
            texto=texto
        )
        return JsonResponse({
            'status': 'ok',
            'mensaje': {
                'id': mensaje.id,
                'emisor': mensaje.emisor.username,
                'es_mío': True,
                'texto': mensaje.texto,
                'hora': mensaje.fecha_envio.strftime('%H:%M')
            }
        })
    return JsonResponse({'error': 'Mensaje vacío'}, status=400)

from django.db.models import Q  # 👈 Asegúrate de tener Q importado arriba

@login_required
def mis_conversaciones(request):
    """Devuelve la lista de conversaciones donde el usuario actual es comprador o vendedor."""
    conversaciones = Conversacion.objects.filter(
        Q(comprador=request.user) | Q(vendedor=request.user)
    ).order_by('-creado_en')

    data = []
    for c in conversaciones:
        # Determinar cuál es el usuario con el que estamos chateando
        otro_usuario = c.vendedor if request.user == c.comprador else c.comprador
        ultimo_msg = c.mensajes.last()
        
        data.append({
            'id': c.id,
            'otro_usuario_id': otro_usuario.id,
            'otro_usuario_nombre': otro_usuario.get_full_name() or otro_usuario.username,
            'ultimo_mensaje': ultimo_msg.texto if ultimo_msg else 'Sin mensajes aún',
            'hora': ultimo_msg.fecha_envio.strftime('%H:%M') if ultimo_msg else ''
        })
        
    return JsonResponse({'conversaciones': data})