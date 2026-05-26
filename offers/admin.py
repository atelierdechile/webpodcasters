from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("product", "is_active", "start_date", "end_date", "tipo", "detalle", "created_at")
    list_filter = ("is_active", "start_date", "end_date")
    search_fields = ("product__title",)

    def tipo(self, obj):
        if obj.is_2x1:
            return "2x1"
        if obj.discount_price:
            return "Precio fijo"
        if obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        return "—"

    def detalle(self, obj):
        if obj.discount_price:
            return f"${obj.discount_price:,.0f}"
        if obj.discount_percentage:
            return f"-{obj.discount_percentage}%"
        return "—"
