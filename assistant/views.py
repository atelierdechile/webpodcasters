import json
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import date
from product.models import Product
from .models import UserQuestion, DailySummaryQuestion

genai.configure(api_key=settings.GEMINI_API_KEY)





SYSTEM_PROMPT = """
Eres un asistente amable y útil para un marketplace de pizzas.
Responde de forma breve, clara y amigable.

Puedes ayudar con:
- Pizzas disponibles
- Precios y ofertas
- Preferencias del usuario (vegano, etc.)
- Problemas comunes (carrito, login, filtros)
- Información general del sitio

No inventes datos. Si el usuario pregunta por productos, usa solo la lista entregada desde el sistema.
"""

FEEDBACK_PROMPT = """
Tu tarea es analizar el texto que el usuario escribió, que puede contener dudas, reclamos o comentarios mezclados.

Devuelve SOLO una pregunta concreta que represente la duda principal del usuario.

Reglas:
- La salida debe ser solo UNA pregunta corta.
- No respondas la pregunta.
- No agregues explicaciones.
- No inventes información.
- Si hay varias ideas, elige la más relevante.
"""

DAILY_SUMMARY_PROMPT = """
A continuación tienes una lista de dudas, problemas o comentarios enviados por usuarios hoy.

Debes generar un RESUMEN BREVE (máximo 50 palabras) que describa:
- Las dudas más frecuentes
- Los problemas comunes
- Cualquier inquietud repetida o relevante

No inventes nada. No hagas preguntas. SOLO devuelve un párrafo muy corto y claro.
"""

CLASSIFY_GREETING_PROMPT = """
Decide si el siguiente mensaje es un saludo.

Un saludo puede ser formal o informal, largo o repetido, por ejemplo:
"hola", "holaaa", "holi", "buenas", "hey", "hello", "holaaaaaaa como estas??" etc.

Responde SOLO con:
- "SALUDO" si el mensaje es un saludo.
- "OTRO" si NO es un saludo.
"""




#  FEEDBACK (guarda dudas resumidas)

@login_required
@csrf_exempt
def feedback_api(request):
    data = json.loads(request.body or "{}")
    msg = data.get("message", "").strip()

    if not msg:
        return JsonResponse({"error": "Mensaje vacío"}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Debes estar logueado"}, status=403)

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # CLASIFICACIÓN: ¿ES SALUDO O NO?
        classify = model.generate_content([
            CLASSIFY_GREETING_PROMPT,
            f"Mensaje: {msg}"
        ]).text.strip().upper()

        if "SALUDO" in classify:
            return JsonResponse({
                "reply": "¡Hola! 👋 ¿Cómo estás? Cuéntame tus dudas o lo que quieras mejorar en nuestra página 💛"
            })

        # SI NO ES SALUDO → es feedback real
        ai_response = model.generate_content([
            FEEDBACK_PROMPT,
            msg
        ])

        summary = ai_response.text.strip()

        UserQuestion.objects.create(
            user=request.user,
            original_text=msg,
            summarized_question=summary
        )

        return JsonResponse({
            "reply": "Gracias por tu comentario 💛 Lo registramos para mejorar nuestra página.",
            "saved_question": summary
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



#  VISTA ADMIN (ver resumen diario)

def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def user_questions_view(request):
    latest_summary = DailySummaryQuestion.objects.order_by("-date").first()

    return render(request, "assistant/user_questions.html", {
        "latest_summary": latest_summary,
    })


# GENERAR RESUMEN DEL DÍA

@login_required
@user_passes_test(is_admin)
def generate_daily_summary(request):
    today = timezone.now().date()
    questions = UserQuestion.objects.filter(created_at__date=today)

    if not questions.exists():
        messages.warning(request, "No hay preguntas registradas hoy.")
        return redirect("/assistant/questions/")

    all_texts = "\n".join([q.summarized_question for q in questions])

    prompt = f"""
    Estas son las preguntas de usuarios del día {today}:

    {all_texts}

    Genera un párrafo de máximo 50 palabras que resuma
    las dudas, inquietudes y problemas más comunes del día.
    """

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    summary = response.text.strip()

    DailySummaryQuestion.objects.update_or_create(
        date=today,
        defaults={
            "summary_question": summary,
            "raw_data": all_texts
        }
    )

    messages.success(request, "Resumen generado correctamente.")
    return redirect("/assistant/questions/")





def summary_by_date(request):
    selected_date = request.GET.get("date")
    summaries = None

    if selected_date:
        summaries = DailySummaryQuestion.objects.filter(date=selected_date)

    return render(request, "assistant/summary_by_date.html", {
        "selected_date": selected_date,
        "summaries": summaries
    })


def daily_summary_panel(request):
    today = date.today()
    latest_summary = DailySummaryQuestion.objects.filter(date=today).first()

    # 🔍 Buscar por fecha si viene del formulario GET
    selected_date = request.GET.get("date")
    summaries_by_date = None

    if selected_date:
        summaries_by_date = DailySummaryQuestion.objects.filter(date=selected_date)

    return render(request, "assistant/user_questions.html", {
        "latest_summary": latest_summary,
        "selected_date": selected_date,
        "summaries_by_date": summaries_by_date,
    })