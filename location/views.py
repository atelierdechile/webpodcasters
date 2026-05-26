
from django.http import JsonResponse
from .models import Provincia, Comuna

def cargar_provincias(request):
    region_id = request.GET.get('region_id')
    provincias = Provincia.objects.filter(region_id=region_id).order_by('nombre')
    data = list(provincias.values('id', 'nombre'))
    return JsonResponse(data, safe=False)

def cargar_comunas(request):
    provincia_id = request.GET.get('provincia_id')
    comunas = Comuna.objects.filter(provincia_id=provincia_id).order_by('nombre')
    data = list(comunas.values('id', 'nombre'))
    return JsonResponse(data, safe=False)
