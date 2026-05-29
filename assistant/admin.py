from django.contrib import admin
from .models import UserQuestion, DailySummaryQuestion

@admin.register(UserQuestion)
class UserQuestionAdmin(admin.ModelAdmin):
    # Mostramos quién preguntó, la versión limpia de la IA y la fecha
    list_display = ("user", "short_question", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("original_text", "summarized_question", "user__username")
    # Solo lectura para proteger el historial de consultas
    readonly_fields = ("user", "original_text", "summarized_question", "created_at")

    @admin.display(description="Pregunta (IA)")
    def short_question(self, obj):
        return obj.summarized_question[:60] + "..." if len(obj.summarized_question) > 60 else obj.summarized_question


@admin.register(DailySummaryQuestion)
class DailySummaryQuestionAdmin(admin.ModelAdmin):
    # Historial de resúmenes diarios por fecha
    list_display = ("date", "short_summary", "created_at")
    list_filter = ("date",)
    search_fields = ("summary_question", "raw_data")
    readonly_fields = ("date", "summary_question", "raw_data", "created_at")

    @admin.display(description="Resumen Diario")
    def short_summary(self, obj):
        return obj.summary_question[:60] + "..." if len(obj.summary_question) > 60 else obj.summary_question