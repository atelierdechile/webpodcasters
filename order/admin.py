from django.contrib import admin
from .models import Order, OrderItem

#Mostrar los ítems de la orden en línea dentro del panel de la orden
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'vendor', 'price', 'quantity', 'get_total_price')

    def get_total_price(self, obj):
        return obj.price * obj.quantity
    get_total_price.short_description = "Total"

# Configurar cómo se muestra la orden
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'paid_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'email')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]
