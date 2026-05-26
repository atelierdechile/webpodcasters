from django.urls import path
from . import views
from .views import summary_by_date

app_name = "assistant"

urlpatterns = [

    path("feedback/", views.feedback_api, name="feedback"),
    path("questions/", views.user_questions_view, name="user_questions"),

    # Vista principal del panel donde está el template que nos mostraste
    path("panel/", views.daily_summary_panel, name="daily_summary_panel"),

    # Generar resumen del día
    path("generate_summary/", views.generate_daily_summary, name="generate_daily_summary"),
    path("questions/generate-summary/", views.generate_daily_summary, name="generate_daily_summary"),

    # (esta queda obsoleta si ya no necesitas otro template)
    path("resumenes-por-fecha/", summary_by_date, name="summary_by_date"),
]
