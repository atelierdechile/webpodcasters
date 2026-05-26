from django.db import models
from django.contrib.auth.models import User


class UserActionLog(models.Model):
    """Registro de acciones de usuario en el sitio y el bot."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_name = models.CharField(max_length=150, blank=True, null=True)
    action = models.TextField()
    page = models.CharField(max_length=100, blank=True, null=True)      
    section = models.CharField(max_length=100, blank=True, null=True)   
    product_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else (self.user_name or "Anónimo")
        return f"{username} - {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

