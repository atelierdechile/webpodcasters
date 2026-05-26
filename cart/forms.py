
from django import forms

class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Nicolás'})
    )
    last_name = forms.CharField(
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'input'})
    )
    phone = forms.CharField(
        label='Teléfono',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    address = forms.CharField(
        label='Dirección',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    zipcode = forms.CharField(
        label='Código Postal',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    place = forms.CharField(
        label='Ciudad / Localidad',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )


