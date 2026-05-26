from django.core.management.base import BaseCommand
from vendor.models import Profile
from vendor.geocoding import geocode_address

class Command(BaseCommand):
    help = "Geocodifica perfiles que no tengan lat/lng"

    def handle(self, *args, **options):
        qs = Profile.objects.select_related("comuna", "region", "country").filter(lat__isnull=True, lng__isnull=True)

        for p in qs:
            comuna = getattr(p.comuna, "name", str(p.comuna) if p.comuna else "")
            region = getattr(p.region, "name", str(p.region) if p.region else "")
            country = getattr(p.country, "name", "Chile")

            try:
                lat, lng = geocode_address(p.address, comuna=comuna, region=region, country=country)
                if lat and lng:
                    p.lat = lat
                    p.lng = lng
                    p.save(update_fields=["lat", "lng"])
                    self.stdout.write(self.style.SUCCESS(f"OK {p.user.username} -> {lat},{lng}"))
                else:
                    self.stdout.write(self.style.WARNING(f"NO RESULT {p.user.username}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERROR {p.user.username}: {e}"))
