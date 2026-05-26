from django.contrib import admin
from .models import (
    Category,
    Product,
    Ingredient,
    ProductIngredient,
    IngredientCategory,
)


# -----------------------------------------------------------
# CATEGORY (categoría de productos: pizzas, bebidas, etc.)
# -----------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "ordering")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("ordering",)


# -----------------------------------------------------------
# INGREDIENT CATEGORY (Quesos, Carnes, Vegetales, etc.)
# -----------------------------------------------------------
@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "ordering")
    ordering = ("ordering", "name")
    prepopulated_fields = {"slug": ("name",)}


# -----------------------------------------------------------
# INGREDIENT
# -----------------------------------------------------------
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("name",)}


# -----------------------------------------------------------
# INLINE de ProductIngredient (tabla intermedia)
# Esto permite agregar ingredientes desde la pantalla del producto
# -----------------------------------------------------------
class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1  # muestra 1 fila vacía para agregar más
    autocomplete_fields = ["ingredient"]  # búsqueda rápida de ingredientes
    verbose_name = "Ingrediente"
    verbose_name_plural = "Ingredientes"


# -----------------------------------------------------------
# PRODUCT
# -----------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "vendor", "get_ingredients", "category")
    search_fields = ("title", "description")
    list_filter = ("category", "vendor", "preferences")
    prepopulated_fields = {"slug": ("title",)}

    # Inline para agregar ingredientes dentro del producto
    inlines = [ProductIngredientInline]

    def get_ingredients(self, obj):
        """Muestra ingredientes como texto en la tabla del admin."""
        return ", ".join(obj.ingredients.values_list("name", flat=True)) or "-"
    get_ingredients.short_description = "Ingredientes"
