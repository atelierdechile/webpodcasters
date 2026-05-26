import uuid
import json
import secrets
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from product.models import Product
from cart.cart import Cart
from vendor.models import Profile
from botapi.models import TempCart, TempItem, LoginToken


# 🛒 Crear carrito temporal
@csrf_exempt
def create_cart(request):
    phone = request.GET.get("phone")
    token = str(uuid.uuid4())

    if phone:
        TempCart.objects.filter(phone=phone).delete()
        TempCart.objects.create(token=token, phone=phone)
    else:
        TempCart.objects.create(token=token)

    return JsonResponse({"token": token})


# Registrar o verificar usuario
@csrf_exempt
def check_user(request):
    phone = request.GET.get("phone")

    if not phone:
        return JsonResponse({'error': 'No phone provided'}, status=400)

    try:
        user = User.objects.select_related('profile').get(profile__phone=phone)
        return JsonResponse({
            'status': 'registered',
            'name': user.first_name or user.username
        })
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'not_registered',
            'name': ''
        })


# 🍕 LISTADO DE PIZZAS (WhatsApp-friendly)
@csrf_exempt
def pizzas_cards(request):
    pizzas = Product.objects.all().order_by("id")

    if not pizzas.exists():
        return JsonResponse({"text": "No hay pizzas disponibles en este momento."}, safe=False)

    generic_image_url = "https://nonfimbriate-usha-aerobically.ngrok-free.dev/media/generics/pizza_generic.jpg"
    message = "🍕 *Estas son nuestras pizzas disponibles:*\n\n"

    for p in pizzas:
        final_price = p.final_price

        if p.active_offer:
            message += (
                f"{generic_image_url}\n"
                f"🔥 *{p.title}* — *OFERTA*\n"
                f"💵 Precio oferta: *{final_price:,.0f} CLP*\n"
                f"❌ Antes: {p.price:,.0f} CLP\n"
                f"➡️ Escribe *{p.id}* para agregarla al carrito.\n"
                f"──────────────────────────────\n"
            )
        else:
            message += (
                f"{generic_image_url}\n"
                f"🧀 *{p.title}*\n"
                f"💵 Precio: *{final_price:,.0f} CLP*\n"
                f"➡️ Escribe *{p.id}* para agregar esta pizza al carrito.\n"
                f"──────────────────────────────\n"
            )

    message += "\n🛒 Cuando termines, escribe *ver carrito* para revisar tu pedido."
    return JsonResponse({"text": message}, safe=False)


# 📥 Agregar al carrito temporal
@csrf_exempt
def add_to_cart(request):
    data = {}
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = request.POST.dict()
    elif request.method == "GET":
        data = request.GET.dict()

    token = data.get("token")
    product_id = data.get("product_id") or data.get("message_text")
    quantity = data.get("quantity", 1)

    if not token:
        return JsonResponse({"status": "error", "message": "⚠️ No se encontró carrito."})

    if isinstance(product_id, str):
        product_id = product_id.strip().replace("add_", "").strip()

    try:
        product_id = int(product_id)
    except:
        return JsonResponse({"status": "error", "message": "ID inválido."})

    try:
        quantity = max(1, int(quantity))
    except:
        quantity = 1

    try:
        cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Carrito no encontrado."})

    # Producto real
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Producto no existe."})

    item, created = TempItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    # 🟩 Respuesta con precio real (considera oferta)
    final_price = product.final_price

    if product.active_offer:
        msg = (
            f"🔥 *{product.title}* agregada al carrito (x{item.quantity})\n"
            f"💵 Precio oferta: *{final_price:,.0f} CLP*"
        )
    else:
        msg = f"✅ {product.title} agregada al carrito (x{item.quantity}) — {final_price:,.0f} CLP"

    return JsonResponse({"status": "success", "message": msg})


# 🛍 Ver carrito temporal
@csrf_exempt
def view_cart(request):
    token = request.GET.get("token")

    try:
        cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        return JsonResponse({"text": "❌ Carrito no encontrado."})

    items = cart.items.select_related("product")
    if not items.exists():
        return JsonResponse({"text": "🛒 Tu carrito está vacío."})

    message = "🛒 *Tu carrito actual:*\n\n"
    total = 0

    for i in items:
        final_price = i.product.final_price
        subtotal = final_price * i.quantity
        total += subtotal

        if i.product.active_offer:
            message += (
                f"🔥 *{i.product.title}*\n"
                f"Cantidad: {i.quantity}\n"
                f"Precio oferta: {final_price:,.0f} CLP\n"
                f"Subtotal: {subtotal:,.0f} CLP\n"
                f"────────────────────────────\n"
            )
        else:
            message += (
                f"🧀 *{i.product.title}*\n"
                f"Cantidad: {i.quantity}\n"
                f"Precio: {final_price:,.0f} CLP\n"
                f"Subtotal: {subtotal:,.0f} CLP\n"
                f"────────────────────────────\n"
            )

    message += f"\n💰 *Total: {total:,.0f} CLP*\n"
    message += "👉 Escribe *pagar pedido* para finalizar."

    return JsonResponse({"status": "success", "text": message})


# 💳 Generar link de pago (con login automático)
@csrf_exempt
def pay_order(request):
    data = request.GET.dict() or request.POST.dict()
    token = data.get("token")
    phone = data.get("phone")

    try:
        temp_cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Carrito no encontrado."})

    try:
        profile = Profile.objects.get(phone=phone)
        user = profile.user
    except Profile.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Usuario no registrado."})

    login_token = secrets.token_urlsafe(32)
    expires = timezone.now() + timedelta(minutes=5)

    LoginToken.objects.create(user=user, token=login_token, expires_at=expires)

    auto_url = (
        "https://nonfimbriate-usha-aerobically.ngrok-free.dev/"
        f"api/auto-login/{login_token}/?temp_token={token}"
    )

    # Calcular total real (con ofertas)
    items = temp_cart.items.all()
    total = sum(i.product.final_price * i.quantity for i in items)

    msg = (
        f"🧾 *Total a pagar:* {total:,.0f} CLP\n\n"
        f"👉 Completa tu pedido aquí:\n{auto_url}\n\n"
        "⏳ Link válido por 5 minutos."
    )

    return JsonResponse({"status": "success", "message": msg})


# 🔐 Login automático → transfiere carrito
@csrf_exempt
def auto_login(request, token):
    record = get_object_or_404(LoginToken, token=token)
    temp_token = request.GET.get("temp_token")

    if not record.is_valid():
        return HttpResponse("⚠️ Token expirado.", status=403)

    user = record.user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    request.session.save()

    if temp_token:
        try:
            temp_cart = TempCart.objects.get(token=temp_token)
            temp_items = temp_cart.items.all()

            cart = Cart(request)
            for i in temp_items:
                cart.add(i.product.id, i.quantity, update_quantity=False)

            cart.save()
            temp_items.delete()
            temp_cart.delete()

        except TempCart.DoesNotExist:
            pass

    return redirect("/cart/")
