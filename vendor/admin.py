from django.contrib import admin
from .models import Vendor

from .models import Profile,  Allergy
from .models import VendorWeeklyMenu

admin.site.register(Vendor)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'country', 
        'region', 
        'provincia', 
        'comuna', 
        'phone', 
        'address', 
        'zipcode', 
        'created_at'
    )
    list_filter = ('country', 'region', 'provincia', 'comuna')
    search_fields = ('user__username', 'user__email', 'phone', 'address')
    ordering = ('user__username',)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")
    filter_horizontal = ("ingredients",)


@admin.register(VendorWeeklyMenu)
class VendorWeeklyMenuAdmin(admin.ModelAdmin):
    list_display = ("vendor", "date", "product", "created_at")
    list_filter = ("vendor", "date")
    search_fields = ("vendor__name", "product__name")
