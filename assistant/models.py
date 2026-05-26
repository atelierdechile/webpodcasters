from django.db import models
from django.contrib.auth.models import User

class UserQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_text = models.TextField()        # lo que escribió el usuario
    summarized_question = models.TextField()  # pregunta concreta generada por la IA
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.summarized_question[:50]}"

from django.db import models

class DailySummaryQuestion(models.Model):
    date = models.DateField(unique=True)
    summary_question = models.TextField()
    raw_data = models.TextField()  # todas las preguntas concatenadas
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.summary_question[:50]}"
