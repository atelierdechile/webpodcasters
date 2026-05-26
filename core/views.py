from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
import json

from product.models import Product
from core.models import Country
from cart.cart import Cart
from analytics.utils import log_event
from product.views import get_active_comuna




# PAGINA PRINCIPALL

from product.utils import aplicar_preferencias

def frontpage(request):
    countries = Country.objects.all()
    selected_country = request.GET.get('country')
    if selected_country:
        request.session['selected_country'] = selected_country
    else:
        selected_country = request.session.get('selected_country')

    newest_products = Product.objects.all().order_by('-id')

    if not request.user.is_authenticated:
        if selected_country:
            try:
                country = Country.objects.get(id=selected_country)
                newest_products = newest_products.filter(
                    vendor__created_by__profile__country=country
                )
            except Country.DoesNotExist:
                newest_products = []
        else:
            newest_products = []
    else:
        profile = getattr(request.user, "profile", None)
        if profile and profile.country:
            user_country = profile.country
            newest_products = newest_products.filter(
                vendor__created_by__profile__country=user_country
            )
            selected_country = user_country.id
            request.session['selected_country'] = user_country.id

    comuna_activa = get_active_comuna(request)
    if comuna_activa:
        newest_products = newest_products.filter(
            vendor__created_by__profile__comuna__nombre__iexact=comuna_activa
        )

    # ⭐ Aquí agregas la línea que faltaba
    solo_pref = request.GET.get("solo_pref") == "1"
    newest_products = aplicar_preferencias(request.user, newest_products, solo_pref)

    return render(request, "core/frontpage.html", {
        "countries": countries,
        "selected_country": selected_country,
        "newest_products": newest_products[:12],
        "comuna": comuna_activa,
        "solo_pref": solo_pref,
    })



#CONTACTO

def contactpage(request):
    return render(request, 'core/contact.html')



# PREFIJO TELEFÓNICO

def get_country_phone_code(request, pk):
    country = Country.objects.get(pk=pk)
    return JsonResponse({'phone_code': country.phone_code})



#REDIRECCIÓN A PRODUCT HOME

def home(request):
    return redirect('product:home')



#ADMIN LANDING

@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_landing(request):
    return render(request, 'core/admin_landing.html')



# LOGIN PERSONALIZADO

class CustomLoginView(LoginView):
    template_name = 'vendor/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user

        messages.success(self.request, f"👋 Bienvenido {user.username}")

        log_event(
            self.request,
            action=f"👤 Usuario inició sesión ({user.username})",
            page="login",
            extra_data={"method": self.request.method}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "⚠️ Usuario o contraseña incorrectos.")
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return reverse_lazy('core:admin_landing')
        elif hasattr(user, 'vendor'):
            return reverse_lazy('vendor:profile')
        else:
            return reverse_lazy('core:home')



#  404 PERSONALIZADO

def custom_404(request, exception=None):
    return render(request, 'core/404.html', status=404)



#  1. Guardar ubicacion manual si se requiere

# @require_POST
# def set_location(request):
#     region = request.POST.get("region")
#     provincia = request.POST.get("provincia")
#     comuna = request.POST.get("comuna")

#     request.session["temp_region"] = region
#     request.session["temp_provincia"] = provincia
#     request.session["temp_comuna"] = comuna

#     return redirect(request.META.get("HTTP_REFERER", "/"))



#  Guardar ubicacion automatica con ajax

@require_POST
def set_location_auto(request):
    data = json.loads(request.body)
    comuna = data.get("comuna")

    # Guardar comuna "temporal" en sesión
    request.session["temp_comuna"] = comuna
    request.session["temp_region"] = None
    request.session["temp_provincia"] = None

    # Limpiar carrito según nueva comuna
    mensaje = limpiar_carrito_por_comuna(request, comuna)

    return JsonResponse({
        "status": "ok",
        "message": mensaje,
    })



# Limpiar productos incompatibles del carrito

def limpiar_carrito_por_comuna(request, nueva_comuna):
    cart = Cart(request)
    productos_eliminados = 0

    # congelar lista antes de modificar
    for item in list(cart):
        product_obj = None
        product_id = None

        #  detectar cómo viene el item del carrito
        if isinstance(item, dict):
            if "product" in item:
                product_obj = item["product"]
            elif "product_id" in item:
                product_id = item["product_id"]
            elif "id" in item:
                product_id = item["id"]
        else:
            
            continue

        if product_obj is None and product_id is not None:
            try:
                product_obj = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue

        if product_obj is None:
            continue

        vendor_comuna = getattr(
            getattr(
                getattr(product_obj.vendor.created_by, "profile", None),
                "comuna",
                None
            ),
            "nombre",
            None
        )

        if not vendor_comuna:
            continue

        if vendor_comuna.lower() != nueva_comuna.lower():
            cart.remove(product_obj.id)
            productos_eliminados += 1

    if productos_eliminados > 0:
        mensaje = f"Se eliminaron {productos_eliminados} productos del carrito por no estar disponibles en {nueva_comuna}."
    else:
        mensaje = f"Ubicación cambiada a {nueva_comuna}."

    messages.warning(request, mensaje)
    return mensaje



