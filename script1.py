import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# ======================================================
# 🔧 CONFIGURAR DJANGO PARA EJECUTAR SCRIPT DIRECTO
# ======================================================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simple_multivendor_site.settings")
django.setup()

# ======================================================
# 📦 IMPORTAR MODELOS
# ======================================================
from order.models import Order, OrderItem
from product.models import Product
from vendor.models import Vendor

# ======================================================
# 🔥 CONFIGURACIÓN
# ======================================================
VENDOR_ID = 17   # Cambia este si quieres otro vendedor
vendor = Vendor.objects.get(id=VENDOR_ID)
products = list(Product.objects.filter(vendor=vendor))

if not products:
    print(f"❌ El vendedor {vendor.name} no tiene productos.")
    exit()

# Ventas a generar
dias_y_ventas = {
    0: 5,    # hoy
    2: 7,    # hace 2 días
    6: 3,    # hace 6 días
    12: 10,  # hace 12 días
    25: 4,   # hace 25 días
}

# ======================================================
# 🚀 GENERAR VENTAS
# ======================================================
print("\n📌 Generando ventas ficticias para el vendedor:", vendor.name)

for dias, cantidad in dias_y_ventas.items():
    fecha = timezone.now() - timedelta(days=dias)
    print(f"\n🟦 {cantidad} ventas del día {fecha.date()}...")

    for _ in range(cantidad):

        # Crear la orden
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

        # Importante: agregar vendor (M2M)
        order.vendors.add(vendor)

        # Forzar fecha personalizada
        order.created_at = fecha
        order.save()

        # Crear item
        product = random.choice(products)
        quantity = random.randint(1, 3)

        OrderItem.objects.create(
            order=order,
            product=product,
            vendor=vendor,
            quantity=quantity,
            price=product.price,
            original_price=product.price,
            discount_percentage=0,
        )

        print(f"   ✔ {product.title} x{quantity}")

print("\n🔥 Ventas generadas correctamente.\n")
