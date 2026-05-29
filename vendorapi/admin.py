from django.contrib import admin
from .models import VendorApiKey

@admin.register(VendorApiKey)
class VendorApiKeyAdmin(admin.ModelAdmin):
    list_display = ("vendor", "is_active", "created_at", "last_used")
    list_filter = ("is_active", "created_at")
    search_fields = ("vendor__name",)
    # SEGURIDAD CLAVE: La clave se genera automáticamente y no debe ser alterada a mano
    readonly_fields = ("key", "created_at", "last_used")