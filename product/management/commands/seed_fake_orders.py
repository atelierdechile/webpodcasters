from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random

from order.models import Order, OrderItem
from product.models import Product
from vendor.models import Vendor

class Command(BaseCommand):
    help = "Crea órdenes falsas para pruebas (últimos 14 días, todas pagadas)"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int, help="Cantidad de órdenes a crear")

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        products = list(Product.objects.all())
        vendors = list(Vendor.objects.all())

        if not products:
            self.stdout.write(self.style.ERROR("No hay productos en la base de datos."))
            return

        if not vendors:
            self.stdout.write(self.style.ERROR("No hay vendors."))
            return

        for _ in range(count):
            # Crear orden con status "paid"
            order = Order.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                address=fake.street_address(),
                zipcode=fake.postcode(),
                place=fake.city(),
                phone=fake.phone_number(),
                paid_amount=random.randint(5000, 50000),
                paid=True,  # aseguramos que esté pagada
                status="paid",
            )

            # Fecha aleatoria en los últimos 14 días
            order.created_at = timezone.now() - timezone.timedelta(days=random.randint(0, 13))
            order.save(update_fields=["created_at"])

            # Añadir vendors aleatorios
            vendor_sample = random.sample(vendors, random.randint(1, min(3, len(vendors))))
            order.vendors.add(*vendor_sample)

            # Crear items
            for _ in range(random.randint(1, 4)):
                product = random.choice(products)
                vendor = random.choice(vendors)
                price = getattr(product, "price", random.randint(1000, 10000))

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    vendor=vendor,
                    price=price,
                    original_price=price,
                    discount_percentage=0,
                    quantity=random.randint(1, 3),
                )

        self.stdout.write(self.style.SUCCESS(f"Se crearon {count} órdenes falsas correctamente (últimos 14 días, todas pagadas)."))
