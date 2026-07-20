from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversacion(models.Model):
    comprador = models.ForeignKey(User, related_name='chats_comprador', on_delete=models.CASCADE)
    vendedor = models.ForeignKey(User, related_name='chats_vendedor', on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversación"
        verbose_name_plural = "Conversaciones"

    def __str__(self):
        return f"Chat #{self.id}: {self.comprador.username} ↔ {self.vendedor.username}"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, related_name='mensajes', on_delete=models.CASCADE)
    emisor = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_envio']
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"

    def __str__(self):
        return f"[{self.fecha_envio.strftime('%d/%m %H:%M')}] {self.emisor.username}: {self.texto[:20]}"