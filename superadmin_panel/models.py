from django.db import models

# Create your models here.
# messaging/models.py
from django.db import models
from django.conf import settings

class VendorMessageLog(models.Model):
    TARGET_ALL = "all"
    TARGET_COMUNA = "comuna"
    TARGET_VENDOR = "vendor"

    target_type = models.CharField(
        max_length=20,
        choices=[
            (TARGET_ALL, "Todos"),
            (TARGET_COMUNA, "Por comuna"),
            (TARGET_VENDOR, "Vendedor específico"),
        ],
    )

    comuna = models.CharField(max_length=120, blank=True, null=True)  # o FK si tienes tabla
    vendor_id = models.IntegerField(blank=True, null=True)  # o FK a Vendor

    subject = models.CharField(max_length=255)
    body = models.TextField()

    attachment = models.FileField(upload_to="admin_vendor_messages/", blank=True, null=True)
    recipients_count = models.PositiveIntegerField(default=0)

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vendor_message_logs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.subject}"
