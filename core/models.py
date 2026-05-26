from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    iso_code = models.CharField(max_length=5, unique=True)
    phone_code = models.CharField(max_length=10)
    mobile_prefix = models.CharField(max_length=5, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=5, default='$')
    #active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone_code})"

