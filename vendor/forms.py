from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from phonenumber_field.formfields import PhoneNumberField
from core.models import Country
from .models import Profile
from product.models import Product 
from location.models import Region, Provincia, Comuna
from .geocoding import geocode_address


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'title', 'category', 'description', 'price', 'image', 
       #     'preferences', 'unidad_tiempo', 'fecha_inicio_arriendo', 'fecha_termino_arriendo'
        ]
        labels = {
            'title': 'Nombre del servicio o equipo',
            'category': 'Categoría',
            'description': 'Descripción',
            'price': 'Precio base de cobro',
            'image': 'Imagen referencial',
            'preferences': 'Intereses / Especialidades relacionadas',
            'unidad_tiempo': 'Métrica de cobro (Tiempo)',
            'fecha_inicio_arriendo': 'Disponible desde',
            'fecha_termino_arriendo': 'Disponible hasta',
        }
        widgets = {
            'preferences': forms.CheckboxSelectMultiple(),
            # Usamos widgets de tipo datetime locales para que aparezca el selector de calendario en el navegador
            'fecha_inicio_arriendo': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_termino_arriendo': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agrega clases CSS automáticas a los widgets 
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput) and not isinstance(field.widget, forms.CheckboxSelectMultiple):
                existing_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing_class + ' input').strip()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(max_length=255, required=True)

    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, label="Región")
    provincia = forms.ModelChoiceField(queryset=Provincia.objects.none(), required=False, label="Provincia")
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.none(), required=False, label="Comuna")

    country = forms.ModelChoiceField(
        queryset=Country.objects.none(),
        empty_label='Selecciona un país',
        required=True,
        widget=forms.Select()
    )

    phone = PhoneNumberField(
        region='CL',
        required=True,
        error_messages={
            'invalid': 'Por favor ingresa un número válido con el código de país.'
        },
        widget=forms.TextInput(attrs={'placeholder': 'Selecciona país primero'})
    )

    address = forms.CharField(max_length=255, required=True)
    zipcode = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'country', 'region', 'provincia', 'comuna',
            'phone', 'address', 'zipcode',
            'password1', 'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['country'].queryset = Country.objects.all().order_by('name')

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['provincia'].queryset = Provincia.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                pass
        if 'provincia' in self.data:
            try:
                provincia_id = int(self.data.get('provincia'))
                self.fields['comuna'].queryset = Comuna.objects.filter(provincia_id=provincia_id)
            except (ValueError, TypeError):
                pass

        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                existing_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing_class + ' input').strip()

        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone': '+56 9 1234 5678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        for name, ph in placeholders.items():
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', ph)

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError("Debes seleccionar un país.")
        return country

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        country = self.cleaned_data.get('country')

        phone_str = str(phone) if phone is not None else ''
        if not country:
            raise forms.ValidationError("Debes seleccionar un país.")

        phone_str = re.sub(r'[^0-9+]', '', phone_str)
        code = country.phone_code.strip()
        prefix = (country.mobile_prefix or '').strip()

        if not phone_str.startswith(code):
            raise forms.ValidationError(
                f"El número debe comenzar con {code} para {country.name}."
            )

        after_code = phone_str[len(code):]
        if prefix and not after_code.startswith(prefix):
            raise forms.ValidationError(
                f"En {country.name} los móviles deben comenzar con {prefix} después de {code}."
            )

        normalized_number = code + after_code
        self.cleaned_data['phone'] = normalized_number
        return normalized_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            comuna_obj = self.cleaned_data.get('comuna')
            region_obj = self.cleaned_data.get('region')
            country_obj = self.cleaned_data.get('country')

            comuna_name = getattr(comuna_obj, "name", str(comuna_obj) if comuna_obj else "")
            region_name = getattr(region_obj, "name", str(region_obj) if region_obj else "")
            country_name = getattr(country_obj, "name", "Chile")

            lat, lng = None, None
            try:
                lat, lng = geocode_address(
                    address=self.cleaned_data["address"],
                    comuna=comuna_name,
                    region=region_name,
                    country=country_name,
                )
            except Exception:
                pass

            Profile.objects.create(
                user=user,
                country=country_obj,
                region=region_obj,
                provincia=self.cleaned_data.get('provincia'),
                comuna=comuna_obj,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                zipcode=self.cleaned_data['zipcode'],
                lat=lat,
                lng=lng,
            )
        return user