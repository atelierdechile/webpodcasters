from django.shortcuts import render, get_object_or_404
from order.models import Order
from django.http import JsonResponse
import requests

def panel_vendedor(request):
    vendor = request.user.vendor
    orders = Order.objects.filter(vendors=vendor).order_by("-created_at")[:50]

    order_id = request.GET.get("order")
    selected_order = None
    items = None

    if order_id:
        selected_order = get_object_or_404(Order, id=order_id, vendors=vendor)
        items = selected_order.items.all()

    return render(request, "vendorpos/panelvendor.html", {
        "orders": orders,
        "selected_order": selected_order,
        "items": items,
        "vendor": vendor,
    })


VALID_STATES = ["accepted", "rejected", "preparing", "ready", "delivered", "cancelled"]


def pos_update_status(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    vendor = request.user.vendor

    new_status = request.POST.get("status")

    if new_status not in VALID_STATES:
        return JsonResponse({"error": "Estado inválido"}, status=400)

    # 🔐 PROTECCIÓN: solo el dueño puede modificar la orden
    order = get_object_or_404(Order, id=order_id, vendors=vendor)

    order.status = new_status
    order.save()

    send_pos_webhook(order, new_status)

    return JsonResponse({"success": True, "new_status": new_status})


def send_pos_webhook(order, status):
    url = "https://webhook.site/b43f9bc4..."  # destino externo

    payload = {
        "order_id": order.id,
        "status": status,
        "items": [
            {
                "product": item.product.title,
                "qty": item.quantity,
                "price": item.price
            }
            for item in order.items.all()
        ]
    }

    try:
        r = requests.post(url, json=payload)
        print("🔥 POS Webhook enviado:", r.status_code)
    except Exception as e:
        print("❌ Error enviando POS webhook:", e)
