from django.contrib import admin
from .models import Region, Provincia, Comuna

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('nombre', 'codigo')

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'region')
    list_filter = ('region',)
    search_fields = ('nombre', 'codigo')

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'provincia')
    list_filter = ('provincia__region', 'provincia') 
    search_fields = ('nombre', 'codigo')