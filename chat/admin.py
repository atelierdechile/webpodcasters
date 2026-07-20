from django.contrib import admin
from .models import Conversacion, Mensaje

class MensajeInline(admin.TabularInline):
    model = Mensaje
    extra = 0
    readonly_fields = ('emisor', 'texto', 'fecha_envio')
    can_delete = False

@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'comprador', 'vendedor', 'creado_en')
    search_fields = ('comprador__username', 'vendedor__username')
    inlines = [MensajeInline]