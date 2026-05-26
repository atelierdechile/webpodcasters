# product/management/commands/load_ingredients.py

from django.core.management.base import BaseCommand
from product.models import Ingredient, IngredientCategory


CATEGORIES = {
    "Bases": [
        "Masa tradicional",
        "Masa delgada",
        "Masa pan",
        "Salsa de tomate",
        "Salsa blanca",
        "Salsa BBQ",
        "Aceite de oliva",
    ],
    "Quesos": [
        "Mozzarella",
        "Queso cheddar",
        "Queso parmesano",
        "Queso gouda",
        "Queso azul",
        "Queso crema",
    ],
    "Carnes": [
        "Pepperoni",
        "Jamón",
        "Tocino",
        "Carne molida",
        "Pollo",
        "Pollo BBQ",
        "Salchicha italiana",
        "Longaniza",
        "Chorizo",
        "Salame",
        "Jamón ahumado",
        "Cerdo desmenuzado",
    ],
    "Vegetales": [
        "Tomate",
        "Cebolla",
        "Cebolla caramelizada",
        "Champiñones",
        "Aceitunas negras",
        "Aceitunas verdes",
        "Pimiento rojo",
        "Pimiento verde",
        "PIMIENTO amarillo",
        "Choclo",
        "Piña",
        "Espinaca",
        "Tomate cherry",
        "Rúcula",
        "Alcachofa",
        "Berenjena",
        "Zucchini",
    ],
    "Premium": [
        "Prosciutto",
        "Pepperoni picante",
        "Carne Angus",
        "Pulled pork",
        "Trufa",
        "Panceta",
        "Queso de cabra",
    ],
    "Extras": [
        "Orégano",
        "Pesto",
        "Salsa picante",
    ],
}


class Command(BaseCommand):
    help = "Reinicia categorías e ingredientes de pizza en la base de datos."

    def handle(self, *args, **kwargs):
        # ---------------------------------------------------
        # 1. ELIMINAR INGREDIENTES Y CATEGORÍAS EXISTENTES
        # ---------------------------------------------------
        self.stdout.write(self.style.WARNING("Eliminando ingredientes existentes..."))
        deleted_ing = Ingredient.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Ingredientes eliminados: {deleted_ing[0]}"))

        self.stdout.write(self.style.WARNING("Eliminando categorías de ingredientes existentes..."))
        deleted_cat = IngredientCategory.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Categorías eliminadas: {deleted_cat[0]}"))

        # ---------------------------------------------------
        # 2. CREAR CATEGORÍAS
        # ---------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\nCreando categorías..."))
        category_objects = {}

        for order, (cat_name, items) in enumerate(CATEGORIES.items(), start=1):
            category = IngredientCategory.objects.create(
                name=cat_name,
                ordering=order,
            )
            category_objects[cat_name] = category
            self.stdout.write(self.style.SUCCESS(f"✔ Categoría creada: {cat_name}"))

        # ---------------------------------------------------
        # 3. CREAR INGREDIENTES ASOCIADOS
        # ---------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\nCreando ingredientes..."))

        ing_count = 0

        for cat_name, items in CATEGORIES.items():
            category = category_objects[cat_name]

            for ing in items:
                obj = Ingredient.objects.create(
                    name=ing,
                    category=category,
                )
                ing_count += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Ingrediente agregado: {ing} → {cat_name}"))

        # ---------------------------------------------------
        # 4. Resumen final
        # ---------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n=== RESUMEN ==="))
        self.stdout.write(self.style.SUCCESS(f"Categorías creadas: {len(CATEGORIES)}"))
        self.stdout.write(self.style.SUCCESS(f"Ingredientes insertados: {ing_count}"))
        self.stdout.write(self.style.SUCCESS("Carga completada correctamente."))
