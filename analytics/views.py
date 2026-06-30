from datetime import timedelta, date
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum, F, IntegerField, ExpressionWrapper
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now, localtime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import UserActionLog
from .utils import classify_section
from vendor.models import Profile, UserPreference, Preference, Vendor
from order.models import Order, OrderItem
import requests
from django.conf import settings

@login_required
def api_buscar_vendedores_google(request):
    # 1. Obtener el perfil del comprador logueado
    perfil_comprador = getattr(request.user, "profile", None)
    
    if not perfil_comprador or not perfil_comprador.comuna:
        return JsonResponse(
            {"error": "Necesitas tener configurada una ubicación en tu perfil para usar esta función."}, 
            status=400
        )
    
    # Capturar el modo de transporte dinámico (?modo=walking, bicycling, etc.)
    modo_transporte = request.GET.get("modo", "driving").strip().lower()
    if modo_transporte not in ["driving", "walking", "bicycling", "transit"]:
        modo_transporte = "driving"

    # Construir origen usando la calle exacta que ya captura tu modelo
    comuna_comp = perfil_comprador.comuna.nombre.strip()
    if perfil_comprador.address:
        origen = f"{perfil_comprador.address.strip()}, {comuna_comp}, Chile"
    else:
        origen = f"{comuna_comp}, Chile"

    # 2. Recopilar todos los vendedores activos
    vendedores = Vendor.objects.select_related("created_by__profile__comuna")
    destinos_lista = []
    vendedores_validos = []

    for v in vendedores:
        perfil_vendedor = getattr(v.created_by, "profile", None)
        if perfil_vendedor and perfil_vendedor.comuna:
            if v.created_by == request.user:
                continue
                
            comuna_vend = perfil_vendedor.comuna.nombre.strip()
            # Si el vendedor tiene dirección exacta, la usamos
            if perfil_vendedor.address:
                dir_vendedor = f"{perfil_vendedor.address.strip()}, {comuna_vend}, Chile"
            else:
                dir_vendedor = f"{comuna_vend}, Chile"
                
            destinos_lista.append(dir_vendedor)
            vendedores_validos.append(v)

    if not destinos_lista:
        return JsonResponse({"error": "No existen creadores con direcciones registradas."}, status=400)

    # 3. Llamada a Google Distance Matrix
    destinos_pipe = "|".join(destinos_lista)
    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)

    if not api_key:
        return JsonResponse({"error": "La credencial GOOGLE_MAPS_API_KEY no está configurada."}, status=500)

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origen,
        "destinations": destinos_pipe,
        "key": api_key,
        "mode": modo_transporte,
        "language": "es"
    }

    vendedores_cercanos = []

    try:
        response = requests.get(url, params=params, timeout=6).json()

        if response.get("status") == "OK":
            elementos = response["rows"][0]["elements"]

            for idx, elemento in enumerate(elementos):
                if elemento.get("status") == "OK":
                    distancia_metros = elemento["distance"]["value"] 
                    distancia_texto = elemento["distance"]["text"]   
                    duracion_texto = elemento["duration"]["text"]    

                    # Filtro de rango de 5 Kilómetros, EDITAR para cambiar el rango de búsqueda
                    if distancia_metros <= 5000:
                        vendedor_match = vendedores_validos[idx]
                        
                        # Extraemos la dirección geográfica limpia del vendedor
                        p_vend = vendedor_match.created_by.profile
                        c_name = p_vend.comuna.nombre.strip()
                        if p_vend.address:
                            direccion_geografica = f"{p_vend.address.strip()}, {c_name}, Chile"
                        else:
                            direccion_geografica = f"{c_name}, Chile"

                        vendedores_cercanos.append({
                            "id": vendedor_match.id,
                            "name": vendedor_match.name,
                            "comuna": c_name.title(),
                            "distancia": distancia_texto,
                            "tiempo": duracion_texto,
                            "modo": modo_transporte,
                            "direccion_real": direccion_geografica # 👈 Enviado limpio al front para el mapa
                        })
        else:
            return JsonResponse({"error": f"Google Maps API retornó un error: {response.get('status')}"}, status=500)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Fallo de conexión: {str(e)}"}, status=500)

    return JsonResponse(vendedores_cercanos, safe=False)

# ============================================================================
# 🗺️ MAPAS Y GEOLOCALIZACIÓN HISTÓRICA
# ============================================================================

@staff_member_required
def map_vendors_sales_today(request):
    today = timezone.localdate()

    total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=IntegerField()
    )

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


# ============================================================================
# 📊 INTERFAZ GRÁFICA Y CONTROL DE LOGS DE ACTIVIDAD
# ============================================================================

@staff_member_required
def dashboard(request):
    """Dashboard técnico con filtros y colores automáticos de actividad."""
    logs = UserActionLog.objects.all()

    tipo = request.GET.get("tipo", "").strip()
    usuario = request.GET.get("usuario", "").strip()
    fecha = request.GET.get("fecha", "").strip()
    page = request.GET.get("page", "").strip()
    section = request.GET.get("section", "").strip()

    if tipo == "global":
        logs = logs.filter(action__icontains="ERROR GLOBAL")
    elif tipo == "error":
        logs = logs.filter(action__icontains="error")
    elif tipo == "accion":
        logs = logs.exclude(action__icontains="error")

    if usuario:
        logs = logs.filter(
            Q(user__username__icontains=usuario) |
            Q(user_name__icontains=usuario)
        )

    if fecha == "hoy":
        logs = logs.filter(timestamp__date=now().date())

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

    if section:
        logs = logs.filter(section__icontains=section)

    logs = logs.order_by("-timestamp")[:400]

    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()
    usuarios = UserActionLog.objects.exclude(user=None).values("user").distinct().count()
    mas_comunes = (
        UserActionLog.objects.exclude(action__icontains="error")
        .values("action")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    for log in logs:
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
    try:
        rango = int(request.GET.get("rango", 7))
        if rango not in [7, 14]:
            rango = 7
    except ValueError:
        rango = 7

    hoy = localtime().date()
    fecha_inicio = hoy - timedelta(days=rango - 1)
    fechas = [fecha_inicio + timedelta(days=i) for i in range(rango)]

    logs_queryset = UserActionLog.objects.filter(
        Q(action__icontains="inició sesión")
        | Q(action__icontains="login")
        | Q(action__icontains="visitó")
        | Q(action__icontains="entró"),
        timestamp__gte=localtime().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=rango-1),
        timestamp__lte=localtime(),
    )

    data_dict = {}
    for log in logs_queryset:
        day = localtime(log.timestamp).date()
        data_dict[day] = data_dict.get(day, 0) + 1

    data_complete = [{"fecha": d.strftime("%Y-%m-%d"), "total": data_dict.get(d, 0)} for d in fechas]

    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()

    return JsonResponse({
        "usuarios": data_complete,
        "errores": errores,
        "total": total,
        "rango": rango,
    })


@staff_member_required
def graficos(request):
    return render(request, "analytics/graficos.html")


@staff_member_required
def analytics_horas(request):
    periodo = request.GET.get("periodo", "historico")
    hoy = localtime().date()

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
    today = localtime()
    month = today.month
    year = today.year

    pref_vegano = Preference.objects.filter(slug="vegana").first()

    veganos_mes = 0
    if pref_vegano:
        veganos_mes = UserPreference.objects.filter(
            preference=pref_vegano,
            action="add",
            timestamp__year=year,
            timestamp__month=month,
        ).count()

    ranking = list(
        UserPreference.objects.filter(action="add")
        .values("preference__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    cambios_mes = UserPreference.objects.filter(
        timestamp__year=year,
        timestamp__month=month,
    ).count()

    return JsonResponse({
        "veganos_mes": veganos_mes,
        "ranking": ranking,
        "cambios_mes": cambios_mes,
    })


# ============================================================================
# 📌 FUNCIONES AUXILIARES Y ENDPOINTS COMPARTIDOS
# ============================================================================

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


# ===================== VENDOR DASHBOARD: Métricas locales del Creador =====================

@login_required
def vendor_sales_data(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range", "7days")

    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)

    end = today

    orders = Order.objects.filter(
        vendors=vendor,
        status__iexact="paid",
        created_at__gte=start,
        created_at__lte=end,
    )

    data_dict = {}
    for order in orders:
        day = timezone.localtime(order.created_at).date()
        data_dict[day] = data_dict.get(day, 0) + 1

    dates = [start.date() + timedelta(days=i) for i in range((end.date() - start.date()).days + 1)]
    data_complete = [{"day": d.strftime("%Y-%m-%d"), "total": data_dict.get(d, 0)} for d in dates]

    return JsonResponse(data_complete, safe=False)


@login_required
def vendor_top_products(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range", "7days")

    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)
    end = today

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


# ============================================================================
# 📊 CONTROL CENTRALIZADO DE LA ADMINISTRACIÓN GLOBAL (CAMBIOS APLICADOS)
# ============================================================================

@staff_member_required
def admin_sales_data(request):
    rango = request.GET.get("range", "7days")
    start, end = get_datetime_range(rango)

    # Buscamos los ítems de compras pagadas en el rango solicitado
    items = OrderItem.objects.filter(
        order__status__iexact="paid",
        order__created_at__gte=start,
        order__created_at__lte=end
    )

    # Reconstrucción cronológica del periodo
    start_date = start.date()
    end_date = end.date()
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    dict_ventas = {}
    dict_arriendos = {}

    for item in items:
        day = item.order.created_at.astimezone().date()
        subtotal = item.price * item.quantity

        if item.product.status == 'ARRIENDO':
            dict_arriendos[day] = dict_arriendos.get(day, 0) + subtotal
        else:
            dict_ventas[day] = dict_ventas.get(day, 0) + subtotal

    data_complete = []
    for d in dates:
        v_monto = dict_ventas.get(d, 0)
        a_monto = dict_arriendos.get(d, 0)
        data_complete.append({
            "day": d.strftime("%Y-%m-%d"),
            "ventas": v_monto,
            "arriendos": a_monto,
            "total": v_monto + a_monto  # Preserva compatibilidad con la gráfica de conteo
        })

    return JsonResponse(data_complete, safe=False)


@staff_member_required
def admin_top_products(request):
    range_value = request.GET.get("range", "7days")

    today = timezone.localtime()
    if range_value == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "7days":
        start = today - timedelta(days=6)
    elif range_value == "30days":
        start = today - timedelta(days=29)
    else:
        start = today - timedelta(days=6)
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


# ============================================================================
# 🏙️ NUEVOS ENDPOINTS Y ARREGLOS DE HOY
# ============================================================================

@staff_member_required
def admin_top_comunas(request):
    # CORRECCIÓN: Usamos solo 'order' y 'product', que son ForeignKeys seguros.
    items = OrderItem.objects.filter(
        order__status__iexact="paid"
    ).select_related('order', 'product')

    comunas_dict = {}
    
    for item in items:
        comuna_nombre = "Sin Especificar"
        comprador_profile = Profile.objects.filter(user__email=item.order.email).select_related('comuna').first()
        
        if comprador_profile and comprador_profile.comuna:
            comuna_nombre = comprador_profile.comuna.nombre.strip().title()
        elif item.order.place:
            comuna_nombre = item.order.place.strip().title()

        if comuna_nombre not in comunas_dict:
            comunas_dict[comuna_nombre] = {"comuna": comuna_nombre, "ventas": 0, "arriendos": 0}

        if item.product.status == 'ARRIENDO':
            comunas_dict[comuna_nombre]["arriendos"] += 1  # 👈 CORREGIDO: Cuenta como 1 transacción
        else:
            comunas_dict[comuna_nombre]["ventas"] += item.quantity

    lista_final = list(comunas_dict.values())
    lista_final.sort(key=lambda x: x["ventas"] + x["arriendos"], reverse=True)

    return JsonResponse(lista_final[:10], safe=False)


@staff_member_required 
def admin_vendedores_ranking(request):
    vendedores = Vendor.objects.all()
    ranking_data = []

    for v in vendedores:
        items_vendor = OrderItem.objects.filter(vendor=v, order__status__iexact="paid")
        
        total_ventas = 0
        total_arriendos = 0
        cant_ventas = 0
        cant_arriendos = 0

        for item in items_vendor:
            subtotal = item.price * item.quantity
            if item.product.status == 'ARRIENDO':
                total_arriendos += subtotal
                cant_arriendos += 1  # 👈 CORREGIDO: Cuenta como 1 transacción
            else:
                total_ventas += subtotal
                cant_ventas += item.quantity

        ranking_data.append({
            "vendedor_id": v.id,
            "vendedor_name": v.name,
            "total_ventas": total_ventas,
            "total_arriendos": total_arriendos,
            "cant_ventas": cant_ventas,
            "cant_arriendos": cant_arriendos,
            "total_general": total_ventas + total_arriendos
        })

    ranking_data.sort(key=lambda x: x["total_general"], reverse=True)
    return JsonResponse(ranking_data, safe=False)


@login_required
def vendor_private_metrics(request):
    try:
        vendor = request.user.vendor
    except Exception:
        return JsonResponse({"error": "No cuentas con un perfil de vendedor activo."}, status=403)

    rango = request.GET.get("range", "7days")
    start, end = get_datetime_range(rango) # Llamada a la función que ya existe en este mismo archivo

    # 1. Histórico Diario de Ingresos
    items = OrderItem.objects.filter(
        vendor=vendor,
        order__status__iexact="paid",
        order__created_at__gte=start,
        order__created_at__lte=end
    )

    dates = [start.date() + timedelta(days=i) for i in range((end.date() - start.date()).days + 1)]
    
    dict_diario = {d: {"ventas": 0, "arriendos": 0} for d in dates}
    for item in items:
        day = item.order.created_at.astimezone().date()
        if day in dict_diario:
            subtotal = item.price * item.quantity
            if item.product.status == 'ARRIENDO':
                dict_diario[day]["arriendos"] += float(subtotal)
            else:
                dict_diario[day]["ventas"] += float(subtotal)

    reporte_diario = [
        {"day": d.strftime("%Y-%m-%d"), "ventas": metrics["ventas"], "arriendos": metrics["arriendos"]}
        for d, metrics in dict_diario.items()
    ]

    # 2. Desglose Geográfico de Clientes de este Vendedor
    all_items_vendor = OrderItem.objects.filter(vendor=vendor, order__status__iexact="paid")
    comunas_dict = {}
    
    for item in all_items_vendor:
        comuna_nombre = "Sin Especificar"
        comprador_profile = Profile.objects.filter(user__email=item.order.email).select_related('comuna').first()
        if comprador_profile and comprador_profile.comuna:
            comuna_nombre = comprador_profile.comuna.nombre.strip().title()

        if comuna_nombre not in comunas_dict:
            comunas_dict[comuna_nombre] = {"comuna": comuna_nombre, "cantidad": 0}
        
        comunas_dict[comuna_nombre]["cantidad"] += item.quantity

    reporte_comunas = list(comunas_dict.values())
    reporte_comunas.sort(key=lambda x: x["cantidad"], reverse=True)

    return JsonResponse({
        "diario": reporte_diario,
        "comunas": reporte_comunas[:5] 
    }, safe=False)

#Devuelve la distribución global entre Ventas y Arriendos para el pie chart
@staff_member_required
def admin_sales_rentals_pie(request):
    items = OrderItem.objects.filter(order__status__iexact="paid")
    
    ventas = 0
    arriendos = 0
    
    for item in items:
        if item.product.status == 'ARRIENDO':
            arriendos += 1  # 👈 CORREGIDO: Cuenta como 1 transacción
        else:
            ventas += item.quantity
            
    total = ventas + arriendos
    porcentaje_ventas = round((ventas / total * 100), 1) if total > 0 else 0
    porcentaje_arriendos = round((arriendos / total * 100), 1) if total > 0 else 0

    return JsonResponse({
        "ventas": ventas,
        "arriendos": arriendos,
        "porcentaje_ventas": porcentaje_ventas,
        "porcentaje_arriendos": porcentaje_arriendos,
        "total": total
    })