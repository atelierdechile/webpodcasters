from django.contrib import admin
from .models import (
    Category,
    Product,
    Ingredient,
    ProductIngredient,
    IngredientCategory,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "ordering")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("ordering",)

@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "ordering")
    ordering = ("ordering", "name")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("name",)}

class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1  
    autocomplete_fields = ["ingredient"]  
    verbose_name = "Ingrediente"
    verbose_name_plural = "Ingredientes"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "vendor", "display_ingredients", "category") # Nombre de función actualizado
    search_fields = ("title", "description")
    list_filter = ("category", "vendor", "preferences")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductIngredientInline]

    # Sintaxis moderna y segura para Render
    @admin.display(description="Ingredientes")
    def display_ingredients(self, obj):
        """Muestra ingredientes como texto en la tabla del admin."""
        return ", ".join(obj.ingredients.values_list("name", flat=True)) or "-"