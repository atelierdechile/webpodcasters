from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("product", "is_active", "start_date", "end_date", "tipo_oferta", "detalle_oferta", "created_at")
    list_filter = ("is_active", "start_date", "end_date")
    search_fields = ("product__title",)

    @admin.display(description="Tipo")
    def tipo_oferta(self, obj):
        if obj.is_2x1:
            return "2x1"
        if obj.discount_price:
            return "Precio fijo"
        if obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        return "—"

    @admin.display(description="Detalle")
    def detalle_oferta(self, obj):
        if obj.discount_price:
            return f"${obj.discount_price:,}" 
        if obj.discount_percentage:
            return f"-{obj.discount_percentage}%"
        if obj.is_2x1:
            return "Lleva 2 paga 1"
        return "—"