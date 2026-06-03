from django import forms
from django.forms.fields import IntegerField
from django.forms.forms import Form


class AddToCartForm(forms.Form):
    # Genera un selector numérico limpio para la cantidad de elementos
    quantity = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'input is-small text-center',
            'style': 'max-width: 60px; border-radius: 4px;',
            'value': '1'
        })
    )