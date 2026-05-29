from django.contrib import admin
from .models import VendorMessageLog

@admin.register(VendorMessageLog)
class VendorMessageLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "subject", "target_type", "recipients_count", "sent_by")
    
    list_filter = ("target_type", "created_at", "sent_by")
    
    search_fields = ("subject", "body")
    
    def get_readonly_fields(self, request, obj=None):
        if obj: # Si el registro ya existe, no se puede modificar nada
            return [f.name for f in self.model._meta.fields]
        return []

    # Opcional: Ocultar el botón de "Guardar y añadir otro" cuando se está revisando un log antiguo
    def has_change_permission(self, request, obj=None):
        return False