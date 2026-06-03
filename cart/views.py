import json
import random
import mercadopago
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q, BooleanField, ExpressionWrapper
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from product.models import Product, Category 
from product.forms import AddToCartForm 
from cart.cart import Cart
from core.models import Country
from product.utils import aplicar_preferencias

# Modelos y formularios adicionales para el correcto funcionamiento del carrito
from .forms import CheckoutForm
from order.utilities import checkout, notify_customer, notify_vendor
from botapi.models import TempCart
from order.models import Order


# ===========================================================
# 🌎 FUNCIÓN CENTRAL PARA OBTENER LA COMUNA ACTIVA
# ===========================================================
def get_active_comuna(request):
    temp = request.session.get("temp_comuna")
    if temp:
        return temp

    user = request.user
    if user.is_authenticated:
        profile = getattr(user, "profile", None)
        if profile and profile.comuna:
            return profile.comuna.nombre

    return None


# ============================================================
# 🛒 VISTA: DETALLE DEL CARRITO (Satisface la ruta principal de urls.py)
# ============================================================
@login_required
def cart_detail(request):
    cart = Cart(request)
    try:
        remove_from_cart = request.GET.get('remove_from_cart', '')
        change_quantity = request.GET.get('change_quantity', '')
        quantity = request.GET.get('quantity', 0)
        add_product = request.GET.get('add_product', '')

        if remove_from_cart:
            cart.remove(remove_from_cart)
            return redirect("cart:cart")

        if change_quantity:
            try:
                quantity = int(quantity)
            except:
                quantity = 1
            cart.add(change_quantity, quantity, update_quantity=True)
            return redirect("cart:cart")

        if add_product:
            prod_obj = Product.objects.filter(pk=add_product).first()
            if prod_obj:
                cart.add(add_product, 1)
            return redirect("cart:cart")

        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                "first_name": request.user.first_name or "",
                "last_name": request.user.last_name or "",
                "email": request.user.email or "",
            }

        if request.method == "POST":
            form = CheckoutForm(request.POST)
            if form.is_valid():
                total = float(cart.get_total_cost())
                data = form.cleaned_data

                order = checkout(
                    request,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email=data["email"],
                    phone=data["phone"],
                    address=data["address"],
                    zipcode=data["zipcode"],
                    place=data["place"],
                    amount=total,
                    send_email=False,
                )

                mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                preference_data = {
                    "items": [
                        {
                            "title": item["product"].title,
                            "quantity": item["effective_qty"],
                            "unit_price": float(item["unit_price"]),
                            "currency_id": "CLP",
                        }
                        for item in cart
                    ],
                    "payer": {
                        "name": data["first_name"],
                        "surname": data["last_name"],
                        "email": data["email"],
                    },
                    "back_urls": {
                        "success": f"{settings.SITE_URL}/cart/success/",
                        "failure": f"{settings.SITE_URL}/cart/failure/",
                        "pending": f"{settings.SITE_URL}/cart/pending/",
                    },
                    "binary_mode": True,
                    "notification_url": f"{settings.SITE_URL}/cart/webhook/",
                    "external_reference": str(order.id),
                }

                result = mp.preference().create(preference_data)
                response = result.get("response", {})
                init_point = response.get("init_point")

                if init_point:
                    return redirect(init_point)
        else:
            form = CheckoutForm(initial=initial_data)

        return render(request, "cart/cart.html", {
            "form": form,
            "cart": cart,
            "mp_public_key": settings.MERCADOPAGO_PUBLIC_KEY,
        })
    except Exception as e:
        raise


# ===========================================================
# 🎙️ VISTA: PRODUCT DETAIL (FICHA DEL ELEMENTO)
# ===========================================================
def product(request, category_slug, product_slug):
    from analytics.utils import log_event

    cart = Cart(request)
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)

    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        if product.vendor.country != request.user.profile.country:
            messages.warning(request, "🚫 Este producto o servicio no está disponible para tu país.")
            return redirect("product:category", category_slug=category_slug)

    comuna_activa = get_active_comuna(request)
    vendor_comuna = getattr(product.vendor.created_by.profile.comuna, "nombre", None)

    if comuna_activa and vendor_comuna and comuna_activa.lower() != vendor_comuna.lower():
        messages.warning(request, f"🚫 Este elemento no cuenta con cobertura o disponibilidad en tu comuna ({comuna_activa}).")
        return redirect("product:category", category_slug=category_slug)

    similar_qs = Product.objects.filter(category=product.category).exclude(id=product.id)
    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        similar_qs = similar_qs.filter(vendor__country=request.user.profile.country)
    if comuna_activa:
        similar_qs = similar_qs.filter(vendor__created_by__profile__comuna__nombre__iexact=comuna_activa)

    similar = list(similar_qs)
    if len(similar) > 4:
        similar = random.sample(similar, 4)

    current_view = f"view_{product.id}"
    if request.method == "GET" and request.session.get("last_product_view") != current_view:
        log_event(request, action=f"👀 Vio producto '{product.title}'", page="product/detail", product_id=product.id, extra_data={"precio_final": product.get_final_price()})
        request.session["last_product_view"] = current_view

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para agregar elementos al carrito.")
            return redirect("product:product", category_slug=category_slug, product_slug=product_slug)

        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            cart.add(product_id=product.id, quantity=quantity, update_quantity=False)
            messages.success(request, "Elemento añadido al carrito correctamente.")
            return redirect("product:product", category_slug=category_slug, product_slug=product_slug)
    else:
        form = AddToCartForm()

    return render(request, "product/product.html", {
        "product": product,
        "similar_products": similar,
        "form": form,
        "currency_symbol": product.vendor.country.currency_symbol,
        "currency_code": product.vendor.country.currency,
        "comuna": comuna_activa,
    })


# ===========================================================
# 📁 VISTA: CATEGORY
# ===========================================================
def category(request, category_slug):
    categoria = get_object_or_404(Category, slug=category_slug)

    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        products = Product.objects.filter(category=categoria, vendor__country=request.user.profile.country)
    else:
        country_id = request.session.get("selected_country")
        if country_id:
            try:
                country = Country.objects.get(id=country_id)
                products = Product.objects.filter(category=categoria, vendor__country=country)
            except Country.DoesNotExist:
                products = Product.objects.none()
        else:
            products = Product.objects.none()

    comuna_activa = get_active_comuna(request)
    if comuna_activa:
        products = products.filter(vendor__created_by__profile__comuna__nombre__iexact=comuna_activa)

    solo_pref = request.GET.get("solo_pref") == "1"
    products = aplicar_preferencias(request.user, products, solo_pref)

    products = products.annotate(
        tiene_oferta=ExpressionWrapper(Q(offer__is_active=True), output_field=BooleanField())
    ).order_by('-tiene_oferta', 'id')

    return render(request, "product/category.html", {
        "category": categoria,
        "products": products,
        "comuna": comuna_activa,
        "solo_pref": solo_pref,
    })


# ===========================================================
# 🔍 VISTA: SEARCH
# ===========================================================
def search(request):
    query = request.GET.get('query', '').strip()
    products = Product.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        products = products.filter(vendor__country=request.user.profile.country)

    comuna_activa = get_active_comuna(request)
    if comuna_activa:
        products = products.filter(vendor__created_by__profile__comuna__nombre__iexact=comuna_activa)

    solo_pref = request.GET.get("solo_pref") == "1"
    products = aplicar_preferencias(request.user, products, solo_pref)

    products = products.annotate(
        tiene_oferta=ExpressionWrapper(Q(offer__is_active=True), output_field=BooleanField())
    ).order_by('-tiene_oferta', 'id')

    return render(request, "product/search.html", {
        "products": products,
        "query": query,
        "comuna": comuna_activa,
        "solo_pref": solo_pref,
    })


# ============================================================
# 💳 VISTAS AUXILIARES REQUERIDAS POR URLS.PY
# ============================================================
@login_required
def success(request):
    cart = Cart(request)
    order = Order.objects.filter(email=request.user.email).order_by("-id").first()
    cart.clear()
    messages.success(request, "✅ Tu pago fue procesado correctamente.")
    return render(request, "cart/success.html", {"order": order})

def failure(request):
    messages.error(request, "❌ El pago fue rechazado o cancelado.")
    return redirect("cart:cart")

def pending(request):
    messages.info(request, "🕓 El pago está pendiente de confirmación.")
    return redirect("cart:cart")

@login_required
def checkout_start(request):
    token = request.GET.get("cart_token")
    if not token:
        return redirect("cart:cart")
    try:
        temp_cart = TempCart.objects.get(token=token)
        cart = Cart(request)
        for item in temp_cart.items.all():
            cart.add(item.product.id, item.quantity)
        temp_cart.delete()
    except TempCart.DoesNotExist:
        pass
    return redirect("cart:cart")

@csrf_exempt
def webhook(request):
    return JsonResponse({"status": "ok"}, status=200)