from datetime import timedelta , date
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q ,Sum
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .models import UserActionLog
from .utils import classify_section
from vendor.models import Profile
from vendor.models import UserPreference, Preference
from django.utils.timezone import now
from django.utils.timezone import localdate
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, localtime
from django.http import JsonResponse
from django.db.models import Sum, F, IntegerField, ExpressionWrapper
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

from vendor.models import Vendor
from order.models import OrderItem


@staff_member_required
def map_vendors_sales_today(request):
    today = timezone.localdate()

    total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=IntegerField()
    )

    # ✅ MISMA LÓGICA QUE EL RESTO DEL DASHBOARD
    # ventas = órdenes con status="paid"
    sales_map = dict(
        OrderItem.objects
        .filter(
            order__status__iexact="paid",
            order__created_at__date=today
        )
        .values("vendor_id")
        .annotate(total=Sum(total_expr))
        .values_list("vendor_id", "total")
    )

    data = []
    vendors = Vendor.objects.select_related("created_by__profile__comuna")

    for v in vendors:
        profile = getattr(v.created_by, "profile", None)
        if not profile or profile.lat is None or profile.lng is None:
            continue

        data.append({
            "id": v.id,
            "name": getattr(v, "name", str(v)),
            "lat": float(profile.lat),
            "lng": float(profile.lng),
            "comuna": str(profile.comuna) if profile.comuna else None,
            "sales_today": int(sales_map.get(v.id, 0)),
        })

    return JsonResponse(data, safe=False)






from order.models import Order, OrderItem




@staff_member_required
def dashboard(request):
    """Dashboard con filtros y colores automáticos."""
    logs = UserActionLog.objects.all()

    # --- FILTROS ---
    tipo = request.GET.get("tipo", "").strip()
    usuario = request.GET.get("usuario", "").strip()
    fecha = request.GET.get("fecha", "").strip()
    page = request.GET.get("page", "").strip()
    section = request.GET.get("section", "").strip()

    # Filtrar por tipo
    if tipo == "global":
        logs = logs.filter(action__icontains="ERROR GLOBAL")
    elif tipo == "error":
        logs = logs.filter(action__icontains="error")
    elif tipo == "accion":
        logs = logs.exclude(action__icontains="error")

    # Filtrar por usuario
    if usuario:
        logs = logs.filter(
            Q(user__username__icontains=usuario) |
            Q(user_name__icontains=usuario)
        )

    # Filtrar por fecha
    if fecha == "hoy":
        logs = logs.filter(timestamp__date=now().date())

    # Filtrar por origen
    if page:
        if page == "web":
            logs = (
                logs.exclude(page__icontains="manychat")
                .exclude(page__icontains="whatsapp")
                .exclude(page__icontains="bot")
                .exclude(action__icontains="manychat")
                .exclude(action__icontains="whatsapp")
                .exclude(action__icontains="bot")
                .exclude(page__icontains="analytics")
            )
        elif page == "manychat":
            logs = logs.filter(
                Q(page__icontains="manychat")
                | Q(action__icontains="manychat")
                | Q(action__icontains="whatsapp")
                | Q(page__icontains="whatsapp")
                | Q(user_name__icontains="bot")
            )
        else:
            logs = logs.filter(page__icontains=page)

    # Filtrar por seccion
    if section:
        logs = logs.filter(section__icontains=section)

    logs = logs.order_by("-timestamp")[:400]

    #  CONTADORES
    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()
    usuarios = UserActionLog.objects.exclude(user=None).values("user").distinct().count()
    mas_comunes = (
        UserActionLog.objects.exclude(action__icontains="error")
        .values("action")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # --- Asignar color de fila y asegurar sección ---
    for log in logs:
        # Si el registro no tiene sección, asignarla
        if not log.section:
            log.section = classify_section(log.page, log.action)

        action_lower = (log.action or "").lower()
        page_lower = (log.page or "").lower()
        user_lower = (log.user_name or "").lower()

        if any(k in action_lower or k in page_lower or k in user_lower for k in ["manychat", "whatsapp", "bot"]) or log.section == "bot":
            log.row_class = "row-bot"
        elif "error" in action_lower or log.section == "errores":
            log.row_class = "row-error"
        else:
            log.row_class = "row-web"

    context = {
        "logs": logs,
        "total": total,
        "errores": errores,
        "usuarios": usuarios,
        "mas_comunes": mas_comunes,
        "tipo": tipo,
        "usuario_filtro": usuario,
        "fecha": fecha,
        "page": page,
        "section": section,
    }

    return render(request, "analytics/dashboard.html", context)


@csrf_exempt
def manychat_log(request):
    """Recibe datos desde ManyChat y guarda logs o errores automáticamente."""
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        event = data.get("event", "Evento desconocido")
        user_data = data.get("user", {})
        user_name = user_data.get("name", "Anónimo")
        phone = user_data.get("phone")
        product_id = data.get("product_id")

        user_obj = None
        if phone:
            profile = Profile.objects.filter(phone=phone).select_related("user").first()
            if profile:
                user_obj = profile.user

        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            page="manychat",
            section="bot",
            action=f"🤖 ManyChat: {event}",
            product_id=product_id,
            extra_data={"source": "Bot WhatsApp", "phone": phone},
        )
        return JsonResponse({"status": "ok"})

    except json.JSONDecodeError as e:
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error JSON inválido desde ManyChat: {str(e)}",
            page="manychat_log",
            section="errores",
        )
        return JsonResponse({"status": "error"}, status=200)

    except Exception as e:
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error general en manychat_log: {str(e)}",
            page="manychat_log",
            section="errores",
        )
        return JsonResponse({"status": "error"}, status=200)
    
@staff_member_required
def analytics_data(request):
    """Devuelve datos para los gráficos de actividad de usuarios.
    Permite filtrar por rango de días 7 o 14.
    """
    try:
        rango = int(request.GET.get("rango", 7))
        if rango not in [7, 14]:
            rango = 7
    except ValueError:
        rango = 7

    hoy = localtime().date()
    fecha_inicio = hoy - timedelta(days=rango - 1)
    fechas = [fecha_inicio + timedelta(days=i) for i in range(rango)]

    # Filtrar logs de login o actividad en el rango
    logs_queryset = UserActionLog.objects.filter(
        Q(action__icontains="inició sesión")
        | Q(action__icontains="login")
        | Q(action__icontains="visitó")
        | Q(action__icontains="entró"),
        timestamp__gte=localtime().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=rango-1),
        timestamp__lte=localtime(),
    )

    # Agrupar manualmente por día (zona local)
    data_dict = {}
    for log in logs_queryset:
        day = localtime(log.timestamp).date()
        data_dict[day] = data_dict.get(day, 0) + 1

    # Completar los días sin datos
    data_completa = [{"fecha": d.strftime("%Y-%m-%d"), "total": data_dict.get(d, 0)} for d in fechas]

    # Totales generales
    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()

    return JsonResponse({
        "usuarios": data_completa,
        "errores": errores,
        "total": total,
        "rango": rango,
    })


@staff_member_required
def graficos(request):
  #  graficos en vivo con chartjs desde mi endpoint  /analytics/api/data/
    return render(request, "analytics/graficos.html")


@staff_member_required
def analytics_horas(request):
    periodo = request.GET.get("periodo", "historico")
    hoy = localtime().date()

    # Filtrar logs según periodo
    if periodo == "diario":
        logs = UserActionLog.objects.filter(
            timestamp__gte=localtime().replace(hour=0, minute=0, second=0, microsecond=0),
            timestamp__lte=localtime()
        )
    elif periodo == "semanal":
        logs = UserActionLog.objects.filter(
            timestamp__gte=localtime() - timedelta(days=7),
            timestamp__lte=localtime()
        )
    elif periodo == "mensual":
        logs = UserActionLog.objects.filter(
            timestamp__gte=localtime() - timedelta(days=30),
            timestamp__lte=localtime()
        )
    else:
        logs = UserActionLog.objects.all()

    # Agrupar por hora manualmente
    horas_dict = {h: 0 for h in range(24)}
    for log in logs:
        hora = localtime(log.timestamp).hour
        horas_dict[hora] += 1

    labels = [f"{h:02d}:00" for h in range(24)]
    values = [horas_dict[h] for h in range(24)]

    return JsonResponse({
        "labels": labels,
        "values": values,
    })


def preferences_kpis(request):
    """
    📊 KPI de preferencias alimentarias
    - Usuarios que activaron 'vegano' este mes
    - Ranking de preferencias (add)
    - Total de cambios de preferencias del mes
    """
    today = localtime()  # asegura timezone local
    month = today.month
    year = today.year

    # Intentar obtener la preferencia "vegana"
    pref_vegano = Preference.objects.filter(slug="vegana").first()

    veganos_mes = 0
    if pref_vegano:
        veganos_mes = UserPreference.objects.filter(
            preference=pref_vegano,
            action="add",
            timestamp__year=year,
            timestamp__month=month,
        ).count()

    # Ranking de preferencias activadas (action="add")
    ranking = list(
        UserPreference.objects.filter(action="add")
        .values("preference__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # Total cambios del mes (add + remove)
    cambios_mes = UserPreference.objects.filter(
        timestamp__year=year,
        timestamp__month=month,
    ).count()

    return JsonResponse({
        "veganos_mes": veganos_mes,
        "ranking": ranking,
        "cambios_mes": cambios_mes,
    })




# ================================================================
# 📌 FUNCIONES COMUNES
# ================================================================
def get_datetime_range(range_value):
    """Devuelve start y end como datetime aware para filtrar correctamente."""
    end = now()
    if range_value == "today":
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = end - timedelta(days=6)
    elif range_value == "30days":
        start = end - timedelta(days=29)
    else:
        start = end - timedelta(days=6)
    return start, end

# ===================== VENDOR DASHBOARD: Ventas por día =====================

@login_required
def vendor_sales_data(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range", "7days")

    # Calcular datetime de inicio y fin
    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)  # fallback 7 días

    end = today

    # Filtrar órdenes pagadas del vendor en el rango
    orders = Order.objects.filter(
        vendors=vendor,
        status__iexact="paid",
        created_at__gte=start,
        created_at__lte=end,
    )

    # Agrupar manualmente por día (zona local)
    data_dict = {}
    for order in orders:
        day = timezone.localtime(order.created_at).date()
        data_dict[day] = data_dict.get(day, 0) + 1

    # Rellenar días sin ventas
    dates = [start.date() + timedelta(days=i) for i in range((end.date() - start.date()).days + 1)]
    data_complete = [{"day": d.strftime("%Y-%m-%d"), "total": data_dict.get(d, 0)} for d in dates]

    return JsonResponse(data_complete, safe=False)

# ===================== VENDOR DASHBOARD: Productos más vendidos =====================
@login_required
def vendor_top_products(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range", "7days")

    # Calcular datetime de inicio y fin
    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)  # fallback 7 días
    end = today

    # Filtrar items de órdenes pagadas del vendor
    items = OrderItem.objects.filter(
        vendor=vendor,
        order__status__iexact="paid",
        order__created_at__gte=start,
        order__created_at__lte=end,
    )

    data = (
        items.values("product__title")
             .annotate(total=Sum("quantity"))
             .order_by("-total")
    )

    return JsonResponse(
        [{"product": d["product__title"], "total": d["total"]} for d in data],
        safe=False
    )


@staff_member_required
def admin_sales_data(request):
    rango = request.GET.get("range", "7days")
    start, end = get_datetime_range(rango)

    orders = Order.objects.filter(
        status__iexact="paid",
        created_at__gte=start,
        created_at__lte=end
    )

    # Generar lista de días
    start_date = start.date()
    end_date = end.date()
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Contar órdenes por día
    data_dict = {}
    for o in orders:
        day = o.created_at.astimezone().date()  # convertir a zona local
        data_dict[day] = data_dict.get(day, 0) + 1

    data_complete = [{"day": d.strftime("%Y-%m-%d"), "total": data_dict.get(d, 0)} for d in dates]

    return JsonResponse(data_complete, safe=False)

# ===================== ADMIN DASHBOARD: Productos más vendidos =====================
@staff_member_required
def admin_top_products(request):
    range_value = request.GET.get("range", "7days")

    # Calcular datetime de inicio y fin
    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)  # fallback 7 días
    end = today

    items = OrderItem.objects.filter(
        order__status__iexact="paid",
        order__created_at__gte=start,
        order__created_at__lte=end,
    )

    data = (
        items.values("product__title")
             .annotate(total=Sum("quantity"))
             .order_by("-total")
    )

    return JsonResponse(
        [{"product": d["product__title"], "total": d["total"]} for d in data],
        safe=False
    )




@staff_member_required
def map_vendors_sales_today(request):
    today = timezone.localdate()

    total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=IntegerField()
    )

    # ✅ MISMA LÓGICA QUE EL RESTO DEL DASHBOARD
    # ventas = órdenes con status="paid"
    sales_map = dict(
        OrderItem.objects
        .filter(
            order__status__iexact="paid",
            order__created_at__date=today
        )
        .values("vendor_id")
        .annotate(total=Sum(total_expr))
        .values_list("vendor_id", "total")
    )

    data = []
    vendors = Vendor.objects.select_related("created_by__profile__comuna")

    for v in vendors:
        profile = getattr(v.created_by, "profile", None)
        if not profile or profile.lat is None or profile.lng is None:
            continue

        data.append({
            "id": v.id,
            "name": getattr(v, "name", str(v)),
            "lat": float(profile.lat),
            "lng": float(profile.lng),
            "comuna": str(profile.comuna) if profile.comuna else None,
            "sales_today": int(sales_map.get(v.id, 0)),
        })

    return JsonResponse(data, safe=False)



@staff_member_required
def map_vendors_sales_total(request):
    total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=IntegerField()
    )

    # 🔥 VENTAS HISTÓRICAS (status paid)
    sales_map = dict(
        OrderItem.objects
        .filter(order__status__iexact="paid")
        .values("vendor_id")
        .annotate(total=Sum(total_expr))
        .values_list("vendor_id", "total")
    )

    data = []
    vendors = Vendor.objects.select_related("created_by__profile__comuna")

    for v in vendors:
        profile = getattr(v.created_by, "profile", None)
        if not profile or profile.lat is None or profile.lng is None:
            continue

        data.append({
            "id": v.id,
            "name": v.name,
            "lat": float(profile.lat),
            "lng": float(profile.lng),
            "comuna": str(profile.comuna) if profile.comuna else None,
            "sales_total": int(sales_map.get(v.id, 0)),
        })

    return JsonResponse(data, safe=False)
