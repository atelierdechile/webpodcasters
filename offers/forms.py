from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Offer


class OfferForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        now = timezone.now()

        # Limpia fechas antiguas de instancias previas
        if self.instance and self.instance.start_date:
            if self.instance.start_date < now - timedelta(minutes=1):
                self.initial["start_date"] = None

        if self.instance and self.instance.end_date:
            if self.instance.end_date < now - timedelta(minutes=1):
                self.initial["end_date"] = None

    class Meta:
        model = Offer
        fields = [
            "discount_percentage",
            "discount_price",
            "is_2x1",
            "start_date",
            "end_date",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()

        discount_percentage = cleaned.get("discount_percentage")
        discount_price = cleaned.get("discount_price")
        is_2x1 = cleaned.get("is_2x1")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")

        offer_instance = self.instance
        product = offer_instance.product if offer_instance and offer_instance.pk else None

        # ==============================
        # INCOMPATIBILIDADES
        # ==============================
        if is_2x1 and (discount_percentage or discount_price):
            raise forms.ValidationError("El 2x1 no es compatible con descuentos.")

        if discount_percentage and discount_price:
            raise forms.ValidationError(
                "Debes elegir entre porcentaje o precio rebajado, no ambos."
            )

        # ==============================
        # VALIDACIÓN DE FECHAS
        # ==============================
        now = timezone.now()  # ← FIX IMPORTANTE

        # Permitimos HOY completo, pero NO fechas realmente en el pasado
        if start_date and start_date < now - timedelta(minutes=2):
            raise forms.ValidationError(
                "La fecha de inicio no puede estar en días pasados."
            )

        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError(
                "La fecha de término debe ser después de la fecha de inicio."
            )

        # ==============================
        # VALIDACIONES NUMÉRICAS
        # ==============================
        if discount_percentage:
            if not (1 <= discount_percentage <= 90):
                raise forms.ValidationError(
                    "El porcentaje de descuento debe estar entre 1% y 90%."
                )

        if discount_price and product:
            if discount_price < 1:
                raise forms.ValidationError("El precio rebajado debe ser mínimo $1.")

            if discount_price >= product.price:
                raise forms.ValidationError(
                    f"El precio rebajado (${discount_price}) debe ser menor que "
                    f"el precio original (${product.price})."
                )

        return cleaned
