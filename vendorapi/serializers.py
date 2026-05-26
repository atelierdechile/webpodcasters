from rest_framework import serializers
from order.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "address",
            "created_at",
            "paid_amount",
            "status",
            "items",
        ]
