from order.models import Order, OrderItem
from product.models import Product
from cart.cart import Cart
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import requests

# =============================
# 📧 EMAIL A VENDEDOR / CREADOR
# =============================
def notify_vendor(order):
    from_email = settings.DEFAULT_FROM_EMAIL

    for vendor in order.vendors.all():
        to_email = vendor.created_by.email
        subject = f'🛒 Nueva orden #{order.id} en tu tienda'
        text_content = f'Hola {vendor.name}, tienes una nueva orden de servicio/arriendo.'
        html = render_to_string(
            'order/email_notify_vendor.html',
            {'order': order, 'vendor': vendor}
        )

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html, 'text/html')
        msg.send()


# =============================
# 📧 EMAIL A CLIENTE / OYENTE
# =============================
def notify_customer(order):
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.email

    subject = f'✅ Confirmación de tu orden #{order.id}'
    text_content = 'Gracias por tu confianza y por apoyar a nuestros creadores.' 
    html = render_to_string(
        'order/email_notify_customer.html',
        {'order': order}
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html, 'text/html')
    msg.send()


# =============================
# 🧾 CHECKOUT (OFERTAS READY)
# =============================
def checkout(
    request,
    first_name,
    last_name,
    email,
    address,
    zipcode,
    place,
    phone,
    amount,
    send_email=True,
):
    # 1️⃣ Crear Orden
    order = Order.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        address=address,
        zipcode=zipcode,
        place=place,
        phone=phone,
        paid_amount=amount,  # total real pagado
    )

    cart = Cart(request)

    # 2️⃣ Crear OrderItems correctamente
    for item in cart:
        product = item["product"]
        quantity = item["quantity"]

        unit_price = product.get_final_price()
        original_price = product.price

        if product.active_offer and product.active_offer.is_2x1:
            effective_qty = (quantity // 2) + (quantity % 2)
            discount_pct = 50  
        else:
            effective_qty = quantity
            discount_pct = 0
            if product.active_offer and product.active_offer.discount_percentage:
                discount_pct = product.active_offer.discount_percentage

        OrderItem.objects.create(
            order=order,
            product=product,
            vendor=product.vendor,
            price=unit_price,
            original_price=original_price,
            discount_percentage=discount_pct,
            quantity=effective_qty, 
        )

        order.vendors.add(product.vendor)

    # 3️⃣ Enviar correos
    if send_email:
        try:
            notify_vendor(order)
            notify_customer(order)
        except Exception as e:
            print(f"⚠️ Error enviando notificaciones: {e}")

    # 4️⃣ Enviar Webhook de integración externa
    send_order_webhook(order)

    # 5️⃣ Devolver orden
    return order


# =============================
# 🔥 WEBHOOK FUNCTION
# =============================
def send_order_webhook(order):
    url = "https://webhook.site/b43f9bc4-5d08-4b71-a250-c5f7e9e818a0"

    payload = {
        "order_id": order.id,
        "vendors": [vendor.name for vendor in order.vendors.all()],
        "total": order.paid_amount,
        "status": "new",
        "created_at": str(order.created_at),
        "items": [
            {
                "product": item.product.title,
                "qty": item.quantity,
                "price": item.price
            }
            for item in order.items.all()
        ]
    }
    headers = {
        "x-api-key": "e8bae2ac9040b1a5da2a1d632f025c001bc88a27ad73cb253b2f52fde90b6167",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("🔥 Webhook enviado:", response.status_code)
    except Exception as e:
        print("❌ Error enviando webhook:", e)

    return order