import json
from django.core.management.base import BaseCommand
from location.models import Region, Provincia, Comuna
from pathlib import Path

class Command(BaseCommand):
    help = 'Carga regiones, provincias y comunas desde archivos locales JSON'

    def handle(self, *args, **kwargs):
        base = Path(__file__).resolve().parent.parent.parent / 'data'

        with open(base / 'regiones.json', encoding='utf-8') as f:
            regiones = json.load(f)
        with open(base / 'provincias.json', encoding='utf-8') as f:
            provincias = json.load(f)
        with open(base / 'comunas.json', encoding='utf-8') as f:
            comunas = json.load(f)

        self.stdout.write(self.style.WARNING("⏳ Cargando datos locales..."))

        for r in regiones:
            region, _ = Region.objects.update_or_create(
                codigo=r["codigo"],
                defaults={"nombre": r["nombre"]}
            )

        for p in provincias:
            try:
                region = Region.objects.get(codigo=p["codigo_padre"])
                Provincia.objects.update_or_create(
                    codigo=p["codigo"],
                    region=region,
                    defaults={"nombre": p["nombre"]}
                )
            except Region.DoesNotExist:
                continue

        for c in comunas:
            try:
                provincia = Provincia.objects.get(codigo=c["codigo_padre"])
                Comuna.objects.update_or_create(
                    codigo=c["codigo"],
                    provincia=provincia,
                    defaults={"nombre": c["nombre"]}
                )
            except Provincia.DoesNotExist:
                continue

        self.stdout.write(self.style.SUCCESS("✅ Datos cargados desde archivos locales correctamente."))
