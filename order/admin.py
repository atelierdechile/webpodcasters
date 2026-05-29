from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'vendor', 'price', 'quantity', 'total_item_price')

    @admin.display(description="Total")
    def total_item_price(self, obj):
        if not obj or obj.price is None:
            return 0
        return obj.price * obj.quantity

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'paid_amount', 'status', 'created_at') # Agregué 'status' que es vital ver de un vistazo
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'first_name', 'last_name', 'email')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]