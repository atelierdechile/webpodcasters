import django
import os
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simple_multivendor_site.settings")
django.setup()

from order.models import Order, OrderItem
from product.models import Product
from vendor.models import Vendor

VENDOR_ID = 17
vendor = Vendor.objects.get(id=VENDOR_ID)
products = list(Product.objects.filter(vendor=vendor))

dias_y_ventas = {
    0: 5,    # hoy
    2: 7,    # hace 2 días
    6: 3,    # hace 6 días
    12: 10,  # hace 12 días
    25: 4,   # hace 25 días
}

for dias, cantidad in dias_y_ventas.items():
    fecha = timezone.now() - timedelta(days=dias)
    print(f"Generando {cantidad} ventas del día {fecha.date()}...")

    for _ in range(cantidad):
        order = Order.objects.create(
            first_name="Test",
            last_name="Test",
            email="test@test.com",
            address="Test",
            zipcode="0000",
            place="Test",
            phone="123",
            status="paid",
        )
        order.created_at = fecha
        order.save()

        product = random.choice(products)

        OrderItem.objects.create(
            order=order,
            product=product,
            vendor=vendor,
            quantity=random.randint(1, 3),
            price=product.price,
            original_price=product.price,
            discount_percentage=0,
        )

print("\n🔥 Ventas generadas correctamente.")
