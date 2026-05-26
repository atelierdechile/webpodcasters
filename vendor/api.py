from django.http import JsonResponse
from django.db.models import Sum, F, IntegerField, ExpressionWrapper
from django.utils import timezone

from vendor.models import Vendor
from order.models import OrderItem


def vendors_sales_today(request):
    today = timezone.localdate()

    total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=IntegerField()
    )

    # ventas por vendor_id hoy
    sales_map = dict(
        OrderItem.objects
        .filter(order__paid=True, order__created_at__date=today)
        .values_list("vendor_id")
        .annotate(total=Sum(total_expr))
        .values_list("vendor_id", "total")
    )

    data = []
    qs = Vendor.objects.select_related("created_by__profile__comuna")

    for v in qs:
        p = getattr(v.created_by, "profile", None)
        if not p or p.lat is None or p.lng is None:
            continue

        data.append({
            "id": v.id,
            "name": str(v),  # o v.name si existe
            "lat": float(p.lat),
            "lng": float(p.lng),
            "comuna": str(p.comuna) if p.comuna else None,
            "sales_today": int(sales_map.get(v.id) or 0),
        })

    return JsonResponse(data, safe=False)
