from django.contrib import admin
from .models import Country

# Register your models here.
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code', 'phone_code', 'currency')
    search_fields = ('name', 'iso_code', 'phone_code')
    