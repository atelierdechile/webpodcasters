import random
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q, BooleanField, ExpressionWrapper

from product.models import Product
from .models import Category
from .forms import AddToCartForm
from cart.cart import Cart
from core.models import Country
from order.utilities import get_allergy_conflicts

from product.utils import aplicar_preferencias


# ===========================================================
#   FUNCIÓN CENTRAL PARA OBTENER LA COMUNA ACTIVA
# ===========================================================
def get_active_comuna(request):

    # 1) Comuna temporal establecida en la homepage
    temp = request.session.get("temp_comuna")
    if temp:
        return temp

    # 2) Comuna del perfil (si existe)
    user = request.user
    if user.is_authenticated:
        profile = getattr(user, "profile", None)
        if profile and profile.comuna:
            return profile.comuna.nombre

    return None


# ===========================================================
#   PRODUCT DETAIL
# ===========================================================
def product(request, category_slug, product_slug):
    from analytics.utils import log_event

    cart = Cart(request)
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)

    # PAÍS
    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        if product.vendor.country != request.user.profile.country:
            messages.warning(request, "🚫 Esta pizza no está disponible en tu país.")
            return redirect("product:category", category_slug=category_slug)

    # COMUNA
    comuna_activa = get_active_comuna(request)
    vendor_comuna = getattr(product.vendor.created_by.profile.comuna, "nombre", None)

    if comuna_activa and vendor_comuna and comuna_activa.lower() != vendor_comuna.lower():
        messages.warning(request, f"🚫 Esta pizza no está disponible en tu comuna ({comuna_activa}).")
        return redirect("product:category", category_slug=category_slug)

    # ============================
    # PRODUCTOS SIMILARES
    # ============================
    similar_qs = Product.objects.filter(category=product.category).exclude(id=product.id)

    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        similar_qs = similar_qs.filter(vendor__country=request.user.profile.country)

    if comuna_activa:
        similar_qs = similar_qs.filter(
            vendor__created_by__profile__comuna__nombre__iexact=comuna_activa
        )

    similar = list(similar_qs)
    if len(similar) > 4:
        similar = random.sample(similar, 4)

    # ============================
    # LOG DE VISTA (GET)
    # ============================
    current_view = f"view_{product.id}"
    if request.method == "GET" and request.session.get("last_product_view") != current_view:
        log_event(
            request,
            action=f"👀 Vio producto '{product.title}'",
            page="product/detail",
            product_id=product.id,
            extra_data={"precio_final": product.get_final_price()}
        )
        request.session["last_product_view"] = current_view

    # ============================
    # POST → AGREGAR AL CARRITO
    # ============================
    if request.method == "POST":

        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para agregar productos al carrito.")
            return redirect("product:product", category_slug=category_slug, product_slug=product_slug)

        form = AddToCartForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data["quantity"]

            # 🔥 CHEQUEO DE ALERGIAS EN LA MISMA PÁGINA
            if hasattr(request.user, "profile"):
                ignore_warning = request.POST.get("ignore_allergy_warning") == "1"
                conflicts = get_allergy_conflicts(request.user.profile, product)

                # Mostrar advertencia en la MISMA página
                if conflicts and not ignore_warning:
                    return render(request, "product/product.html", {
                        "product": product,
                        "form": form,
                        "quantity": quantity,
                        "conflicts": conflicts,
                        "allergy_warning": True,
                        "similar_products": similar,
                        "currency_symbol": product.vendor.country.currency_symbol,
                        "currency_code": product.vendor.country.currency,
                        "comuna": comuna_activa,
                    })

            # Si no hay conflictos o ya aceptó → agregar al carrito
            cart.add(product_id=product.id, quantity=quantity, update_quantity=False)
            messages.success(request, "Producto agregado al carrito.")

            log_event(
                request,
                action=f"🖱️ Seleccionó producto '{product.title}' (x{quantity})",
                page="product/detail",
                product_id=product.id,
                extra_data={
                    "precio_final": product.get_final_price(),
                    "cantidad": quantity
                }
            )

            request.session["last_product_view"] = current_view
            return redirect("product:product", category_slug=category_slug, product_slug=product_slug)

    else:
        # GET normal
        form = AddToCartForm()

    # ============================
    # RENDER FINAL
    # ============================
    return render(request, "product/product.html", {
        "product": product,
        "similar_products": similar,
        "form": form,
        "currency_symbol": product.vendor.country.currency_symbol,
        "currency_code": product.vendor.country.currency,
        "comuna": comuna_activa,
    })


# ===========================================================
#   CATEGORY
# ===========================================================
def category(request, category_slug):
    from analytics.utils import log_event

    categoria = get_object_or_404(Category, slug=category_slug)

    # PAÍS
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

    # COMUNA
    comuna_activa = get_active_comuna(request)
    if comuna_activa:
        products = products.filter(
            vendor__created_by__profile__comuna__nombre__iexact=comuna_activa
        )

    # PREFERENCIAS
    solo_pref = request.GET.get("solo_pref") == "1"
    products = aplicar_preferencias(request.user, products, solo_pref)

    # ORDENAR → primero las ofertas activas
    products = products.annotate(
        tiene_oferta=ExpressionWrapper(Q(offer__is_active=True), output_field=BooleanField())
    ).order_by('-tiene_oferta', 'id')

    log_event(
        request,
        action=f"📂 Entró a la categoría '{categoria.title}'",
        page="product/category",
        extra_data={
            "productos_disponibles": products.count(),
            "productos_en_oferta": products.filter(offer__is_active=True).count()
        }
    )

    return render(request, "product/category.html", {
        "category": categoria,
        "products": products,
        "comuna": comuna_activa,
        "solo_pref": solo_pref,
    })


# ===========================================================
#   SEARCH
# ===========================================================
def search(request):
    from analytics.utils import log_event

    query = request.GET.get('query', '').strip()

    products = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )

    # PAÍS
    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.country:
        products = products.filter(vendor__country=request.user.profile.country)

    # COMUNA
    comuna_activa = get_active_comuna(request)
    if comuna_activa:
        products = products.filter(
            vendor__created_by__profile__comuna__nombre__iexact=comuna_activa
        )

    # PREFERENCIAS
    solo_pref = request.GET.get("solo_pref") == "1"
    products = aplicar_preferencias(request.user, products, solo_pref)

    # ORDENAR → primero las ofertas activas
    products = products.annotate(
        tiene_oferta=ExpressionWrapper(Q(offer__is_active=True), output_field=BooleanField())
    ).order_by('-tiene_oferta', 'id')

    if query:
        log_event(
            request,
            action=f"🔍 Buscó '{query}'",
            page="product/search",
            extra_data={
                "resultados": products.count(),
                "con_oferta": products.filter(offer__is_active=True).count()
            }
        )

    return render(request, "product/search.html", {
        "products": products,
        "query": query,
        "comuna": comuna_activa,
        "solo_pref": solo_pref,
    })
