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
    
    whatsapp = PhoneNumberField(region="CL", blank=True, null=True, help_text="Ej: +56912345678")
    
    horario = models.CharField(max_length=255, blank=True, default="Lunes a Viernes de 09:00 a 18:00")

    address = models.CharField(max_length=255, blank=True, default="")
    zipcode = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    preferences = models.ManyToManyField(Preference, blank=True)

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

        if not self.pk and (self.lat is None or self.lng is None):
            should_geocode = True

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


# ============================================================================
# 📊 SISTEMA DE VALORACIONES Y RESEÑAS (NOTA 1 A 7)
# ============================================================================
class Review(models.Model):
    # 🌟 SOLUCIÓN: Usamos el string "order.OrderItem" en lugar del objeto directo
    order_item = models.OneToOneField("order.OrderItem", related_name="review", on_delete=models.CASCADE)
    
    # Registramos el comprador (User de Django) y el Vendor calificado
    customer = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name="reviews", on_delete=models.CASCADE)
    
    # Escala de notas tradicionales de Chile (1 al 7)
    NOTAS_CHOICES = [(i, f"Nota {i}") for i in range(1, 8)]
    rating = models.IntegerField(choices=NOTAS_CHOICES, help_text="Calificación del 1 al 7")
    
    # Comentario en texto libre
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Nota {self.rating} para {self.vendor.name} por @{self.customer.username}"