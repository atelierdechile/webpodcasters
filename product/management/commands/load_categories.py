from django.core.management.base import BaseCommand
from product.models import Category  # Usamos tu modelo real de categorías

# Definimos las categorías iniciales del Marketplace de Podcasters
CATEGORIES = [
    {"title": "Micrófonos", "ordering": 1, "slug": "microfonos"},
    {"title": "Interfaces & Consolas", "ordering": 2, "slug": "interfaces-consolas"},
    {"title": "Audífonos", "ordering": 3, "slug": "audifonos"},
    {"title": "Software & Licencias", "ordering": 4, "slug": "software-licencias"},
    {"title": "Servicios de Edición", "ordering": 5, "slug": "servicios-edicion"},
    {"title": "Estudios & Arriendo", "ordering": 6, "slug": "estudios-arriendo"},
    {"title": "Accesorios & Cableado", "ordering": 7, "slug": "accesorios-cableado"},
]

class Command(BaseCommand):
    help = "Carga las categorías iniciales para el Marketplace de Podcasters de forma limpia."

    def handle(self, *args, **kwargs):
        # 1. Limpieza inicial para evitar duplicados molestos
        self.stdout.write(self.style.WARNING("Limpiando categorías existentes en el catálogo..."))
        deleted_count = Category.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Categorías removidas de Postgres: {deleted_count[0]}"))

        # 2. Inyección de las nuevas categorías de podcasters
        self.stdout.write(self.style.SUCCESS("\nIndexando catálogo técnico de Podcasters..."))
        created_count = 0

        for cat_data in CATEGORIES:
            Category.objects.create(
                title=cat_data["title"],
                ordering=cat_data["ordering"],
                slug=cat_data["slug"]
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"✔ Categoría indexada: {cat_data['title']} (Orden: {cat_data['ordering']})"))

        # 3. Resumen de ejecución
        self.stdout.write(self.style.SUCCESS("\n=== RESUMEN DE CARGA ==="))
        self.stdout.write(self.style.SUCCESS(f"Total de categorías instaladas: {created_count}"))
        self.stdout.write(self.style.SUCCESS("Entorno inicial de Podcasters desplegado con éxito."))