from django.db import models
from django.utils import timezone
from product.models import Product


class Offer(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="offer")

    # Tipos de oferta
    discount_percentage = models.PositiveIntegerField(null=True, blank=True)
    discount_price = models.PositiveIntegerField(null=True, blank=True)
    is_2x1 = models.BooleanField(default=False)

    # Duración
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Control
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Oferta de {self.product.title} (ID {self.product.id})"

    def is_current(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def get_final_price(self):
        """
        Devuelve el precio final del producto considerando:
        - descuento fijo
        - descuento porcentual
        - precio normal
        - NUNCA retorna 0 (MP lo prohíbe)
        """
        if not self.is_current():
            return self.product.price

        # 🔥 1) Descuento por precio fijo
        if self.discount_price:
            return max(1, self.discount_price)

        # 🔥 2) Descuento porcentual
        if self.discount_percentage:
            final = int(self.product.price * (1 - self.discount_percentage / 100))
            return max(1, final)

        # 🔥 3) Sin descuento (solo 2x1 activo)
        return self.product.price
