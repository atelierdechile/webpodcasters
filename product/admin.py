from django.contrib import admin
from .models import Category, Product  


# --- CATEGORY ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "ordering")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("ordering",)


# --- PRODUCT ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "unidad_tiempo", "vendor", "category") 
    search_fields = ("title", "description")
    
    list_filter = ("category", "vendor", "preferences", "unidad_tiempo") 
    prepopulated_fields = {"slug": ("title",)}