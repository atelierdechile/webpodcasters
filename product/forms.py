from django import forms
from django.forms.fields import IntegerField
from django.forms.forms import Form

class AddToCartForm(forms.Form):
    # Configuramos el campo con las clases y estilos que requiere tu diseño
    quantity = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'input style-qty-input text-center', # <-- Tus clases de Bulma y personalizadas
            'style': 'max-width: 80px; font-weight: 600; border-radius: 8px 0 0 8px;', # <-- Tus dimensiones y bordes
        })
    )

    def __init__(self, *args, **kwargs):
        # Extraemos el status del producto si se pasa al formulario
        product_status = kwargs.pop('product_status', 'VENTA')
        super().__init__(*args, **kwargs)
        
        # Si el producto es para arriendo, cambiamos la etiqueta visual
        if product_status == 'ARRIENDO':
            self.fields['quantity'].label = "Meses a arrendar"
        else:
            self.fields['quantity'].label = "Cantidad"