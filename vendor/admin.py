from django.contrib import admin
from .models import Vendor, Profile, Preference, UserPreference 

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "country", "created_at")
    search_fields = ("name", "created_by__username")
    list_filter = ("country", "created_at")

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
    filter_horizontal = ('preferences',)

@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "preference", "action", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "preference__name")