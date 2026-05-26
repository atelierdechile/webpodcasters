from django.contrib import admin
from .models import TempCart, TempItem


class TempItemInline(admin.TabularInline):
    model = TempItem
    extra = 0
    readonly_fields = ("product", "quantity", "precio_real", "subtotal_display")

    # 🔥 Mostrar el precio real (con oferta aplicada)
    def precio_real(self, obj):
        try:
            return f"${obj.product.final_price:,.0f}"
        except:
            return "—"
    precio_real.short_description = "Precio real"

    # 🔥 Subtotal usando precio final (oferta o precio normal)
    def subtotal_display(self, obj):
        try:
            subtotal = obj.product.final_price * obj.quantity
            return f"${subtotal:,.0f}"
        except:
            return "—"
    subtotal_display.short_description = "Subtotal"


@admin.register(TempCart)
class TempCartAdmin(admin.ModelAdmin):
    list_display = ("token", "created_at", "total_display", "cantidad_total")
    inlines = [TempItemInline]
    readonly_fields = ("token", "created_at")

    # 🔥 Total real del carrito (con ofertas)
    def total_display(self, obj):
        try:
            total = sum(item.product.final_price * item.quantity for item in obj.items.all())
            return f"${total:,.0f}"
        except:
            return "—"
    total_display.short_description = "Total"
