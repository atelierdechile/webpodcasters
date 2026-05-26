import secrets
from django.db import models
from vendor.models import Vendor

def generate_api_key():
    return secrets.token_hex(32)  # 64 caracteres ~ súper segura

class VendorApiKey(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    key = models.CharField(max_length=255, unique=True, default=generate_api_key)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"API Key for {self.vendor.name}"