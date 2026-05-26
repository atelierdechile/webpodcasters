from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.models import Country
from location.models import Region, Provincia, Comuna
from django.utils.text import slugify

from vendor.geocoding import geocode_address


class Preference(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Preferencia"
        verbose_name_plural = "Preferencias"
        ordering = ["name"]


class Allergy(models.Model):
    """
    Alergia alimentaria general (Gluten, Lactosa, Frutos secos, etc.)
    Se asocia a ingredientes concretos (product.Ingredient) y a usuarios vía Profile.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    ingredients = models.ManyToManyField(
        "product.Ingredient",
        related_name="allergies",
        blank=True,
        verbose_name="Ingredientes relacionados",
    )

    class Meta:
        verbose_name = "Alergia"
        verbose_name_plural = "Alergias"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1

            while Allergy.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug

        super().save(*args, **kwargs)


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.OneToOneField(
        User, related_name="vendor", on_delete=models.CASCADE
    )
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_balance(self):
        items = self.items.filter(vendor_paid=False, order__vendors__in=[self.id])
        return sum((item.product.price * item.quantity) for item in items)

    def get_paid_amount(self):
        items = self.items.filter(vendor_paid=True, order__vendors__in=[self.id])
        return sum((item.product.price * item.quantity) for item in items)

    # ✅ properties (usa Profile del usuario)
    @property
    def profile(self):
        return getattr(self.created_by, "profile", None)

    @property
    def lat(self):
        p = self.profile
        return p.lat if p else None

    @property
    def lng(self):
        p = self.profile
        return p.lng if p else None


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)

    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    phone = PhoneNumberField(region="CL", blank=True)
    address = models.CharField(max_length=255, blank=True, default="")
    zipcode = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    preferences = models.ManyToManyField(Preference, blank=True)

    allergies = models.ManyToManyField(
        Allergy,
        blank=True,
        related_name="profiles",
        verbose_name="Alergias alimentarias",
    )

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ["user__username"]

    def _location_signature(self):
        """Detecta cambios relevantes para recalcular coords."""
        return (
            (self.address or "").strip(),
            str(self.comuna_id or ""),
            str(self.region_id or ""),
            str(self.country_id or ""),
        )

    def save(self, *args, **kwargs):
        should_geocode = False

        # 1) Perfil nuevo sin coords
        if not self.pk and (self.lat is None or self.lng is None):
            should_geocode = True

        # 2) Perfil existente: si cambió address/comuna/region/country
        if self.pk:
            try:
                old = Profile.objects.only(
                    "address", "comuna_id", "region_id", "country_id", "lat", "lng"
                ).get(pk=self.pk)

                if old._location_signature() != self._location_signature():
                    should_geocode = True
            except Profile.DoesNotExist:
                should_geocode = True

        if should_geocode:
            try:
                comuna_name = str(self.comuna) if self.comuna else ""
                region_name = str(self.region) if self.region else ""
                country_name = str(self.country) if self.country else "Chile"

                lat, lng = geocode_address(
                    address=(self.address or "").strip(),
                    comuna=comuna_name,
                    region=region_name,
                    country=country_name
                )

                if lat is not None and lng is not None:
                    self.lat = lat
                    self.lng = lng

            except Exception as e:
                # No romper el flujo de registro si la API falla
                print("ERROR GEOCODING Profile.save:", e)

        super().save(*args, **kwargs)


class UserPreference(models.Model):
    ACTIONS = (
        ("add", "add"),
        ("remove", "remove"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.ForeignKey(Preference, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Preferencia del Usuario"
        verbose_name_plural = "Preferencias del Usuario"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.username} - {self.preference.name} - {self.action}"


class VendorWeeklyMenu(models.Model):
    vendor = models.ForeignKey(
        "vendor.Vendor", on_delete=models.CASCADE, related_name="weekly_menus"
    )
    date = models.DateField()
    product = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE, related_name="weekly_menus"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("vendor", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.vendor} - {self.date} - {self.product}"
