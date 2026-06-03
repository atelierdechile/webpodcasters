from io import BytesIO
from PIL import Image
from django.core.files import File
from django.db import models
from vendor.models import Vendor, Preference
from django.utils.text import slugify

class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=55)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name="products", on_delete=models.CASCADE)

    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=55, blank=True, unique=True)
    description = models.TextField(blank=True, null=True)

    price = models.IntegerField()
    added_date = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/', blank=True, null=True)

    # Preferencias / Intereses
    preferences = models.ManyToManyField(Preference, blank=True)

    # ⏱️ --- NUEVOS ATRIBUTOS PARA ARRIENDOS DE EQUIPOS Y SERVICIOS ---
    UNIDAD_TIEMPO_CHOICES = [
        ('HORA', 'Por Hora'),
        ('DIARIO', 'Diario'),
        ('SEMANAL', 'Semanal'),
        ('MENSUAL', 'Mensual'),
    ]
    
    unidad_tiempo = models.CharField(
        max_length=10, 
        choices=UNIDAD_TIEMPO_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Unidad de tiempo para arriendo"
    )

    fecha_inicio_arriendo = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Inicio de disponibilidad"
    )
    fecha_termino_arriendo = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Término de disponibilidad"
    )

    class Meta:
        ordering = ['-added_date']

    def __str__(self):
        return self.title

    # ---------------- SLUG ----------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug

        super().save(*args, **kwargs)

    # ---------------- THUMBNAIL ----------------
    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url

        if self.image:
            self.thumbnail = self.make_thumbnail(self.image)
            self.save()
            return self.thumbnail.url

        return "https://via.placeholder.com/240x180.jpg"

    def make_thumbnail(self, image, size=(300, 200)):
        img = Image.open(image)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, "JPEG", quality=85)

        base_name = image.name.rsplit(".", 1)[0]
        thumb_name = f"{base_name}_thumb.jpg"

        return File(thumb_io, name=thumb_name)

    # ---------------- OFERTAS ----------------
    @property
    def active_offer(self):
        try:
            offer = self.offer  
            return offer if offer.is_current() else None
        except Exception:
            return None

    def has_active_offer(self):
        return self.active_offer is not None

    def get_final_price(self):
        offer = self.active_offer
        if not offer:
            return self.price

        if offer.discount_price:
            return max(1, offer.discount_price)

        if offer.discount_percentage:
            final = int(self.price * (1 - offer.discount_percentage / 100))
            return max(1, final)

        return self.price

    def get_offer_percentage(self):
        offer = self.active_offer
        if not offer:
            return 0

        original = self.price
        final = self.get_final_price()

        if original <= 0:
            return 0

        try:
            pct = round(100 - ((final / original) * 100))
            return max(1, min(pct, 90))
        except Exception:
            return 0