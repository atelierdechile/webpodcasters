# location/forms.py
from django import forms
from .models import Region, Provincia, Comuna

class DireccionForm(forms.Form):
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=True)
    provincia = forms.ModelChoiceField(queryset=Provincia.objects.none(), required=True)
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargamos provincias/comunas si vienen en los datos (al enviar el form)
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
