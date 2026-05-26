from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify  
from .forms import SignUpForm, ProductForm
from .models import Vendor, Profile, Preference, Allergy   # 👈 Allergy aquí
from product.models import Product
from django.contrib import messages
from order.models import  Order
from offers.models import Offer
from offers.forms import OfferForm
import datetime
import json
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import VendorWeeklyMenu
from .week_utils import get_week_range
from vendor.decorators import vendor_required
from django.core.paginator import Paginator



#Registro de cliente
def register_customer_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')  
            else:
                return redirect("vendor:select-preferences")



    else:
        form = SignUpForm()

    # Personalización visual
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'input'
        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'country': 'Selecciona tu país',
            'phone': '+56 9 12345678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        if field_name in placeholders:
            field.widget.attrs['placeholder'] = placeholders[field_name]

    return render(request, 'vendor/become_customer.html', {'form': form})


# Registro de vendedor
def register_vendor_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        store_name = request.POST.get('store_name', '')

        if form.is_valid():
            user = form.save()
            login(request, user)

            profile = Profile.objects.get(user=user)
            country = profile.country

            Vendor.objects.create(
                name=store_name if store_name else user.username,
                created_by=user,
                country=country
            )

            # Redirección condicional
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')
            else:
                return redirect('core:home')
    else:
        form = SignUpForm()

    # Personalización visual
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'input'
        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'country': 'Selecciona tu país',
            'phone': '+56 9 12345678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        if field_name in placeholders:
            field.widget.attrs['placeholder'] = placeholders[field_name]

    return render(request, 'vendor/become_vendor.html', {'form': form})


@login_required
def vendor_admin(request):
    context = {}

    if hasattr(request.user, 'vendor'):
        vendor = request.user.vendor
        products = vendor.products.all()
        orders = vendor.orders.all()

        for order in orders:
            order.vendor_amount = 0
            order.vendor_paid_amount = 0
            order.fully_paid = True

            for item in order.items.all():
                if item.vendor == vendor:

                    # 🔥 PRECIO FINAL CON OFERTA
                    price = item.product.get_final_price()
                    total_item = item.quantity * price

                    if item.vendor_paid:
                        order.vendor_paid_amount += total_item
                    else:
                        order.vendor_amount += total_item
                        order.fully_paid = False

        context['is_vendor'] = True
        context['vendor'] = vendor
        context['products'] = products
        context['orders'] = orders

    else:
        context['is_vendor'] = False
        context['username'] = request.user.username

    return render(request, 'vendor/vendor_admin.html', context)



@login_required
def add_product(request):

    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor  # asigna el vendor dueño del producto
            product.save()                        # aquí se genera el slug automáticamente

            # ⭐ MUY IMPORTANTE — GUARDA M2M (preferences + ingredients)
            form.save_m2m()

            return redirect('vendor:profile')
    else:
        form = ProductForm()

    return render(request, 'vendor/add_product.html', {'form': form})



#Eliminar producto
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    return redirect('vendor:profile')


#Editar información del vendedor
@login_required
def edit_vendor(request):
    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')

    vendor = request.user.vendor

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')

        if name:
            vendor.name = name
        if email:
            vendor.created_by.email = email
            vendor.created_by.save()

        vendor.save()
        return redirect('vendor:vendor-admin')

    return render(request, 'vendor/edit_vendor.html', {'vendor': vendor})


#Lista de vendedores
def vendors(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendors.html', {'vendors': vendors})


#Perfil de un vendedor
def vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    return render(request, 'vendor/vendor.html', {'vendor': vendor})


@login_required
def profile_view(request):
    user = request.user

    # PERFIL DEL VENDEDOR
    if hasattr(user, "vendor"):
        vendor = user.vendor

        products = vendor.products.all()
        items = vendor.items.select_related("order", "product").all()
        orders = (
            Order.objects.filter(items__vendor=vendor)
            .distinct()
            .order_by('-id')
        )

        return render(request, "vendor/vendor_profile.html", {
            "vendor": vendor,
            "products": products,
            "orders": orders,
            "items": items,
        })

    # PERFIL CLIENTE
    profile = user.profile
    preferences = Preference.objects.all()
    allergies = Allergy.objects.all()   # 👈 importa Allergy arriba

    selected_ids = list(profile.preferences.values_list("id", flat=True))
    selected_allergies_ids = list(profile.allergies.values_list("id", flat=True))

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        selected_algs = request.POST.getlist("allergies")

        profile.preferences.set(selected_prefs)
        profile.allergies.set(selected_algs)
        profile.save()

        messages.success(request, "Preferencias y alergias actualizadas correctamente 🍕")
        return redirect("vendor:profile")

    return render(request, "vendor/customer_profile.html", {
        "profile": profile,
        "username": user.username,
        "email": user.email,
        "preferences": preferences,
        "allergies": allergies,
        "selected_ids": selected_ids,
        "selected_allergies_ids": selected_allergies_ids,
    })



@login_required
def select_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()
    allergies = Allergy.objects.all()

    # Si ya tiene preferencias o alergias → saltar onboarding
    if profile.preferences.exists() or profile.allergies.exists():
        return redirect('core:home')

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        selected_allergies = request.POST.getlist("allergies")

        profile.preferences.set(selected_prefs)
        profile.allergies.set(selected_allergies)
        profile.save()

        return redirect('core:home')

    selected_preferences_ids = list(profile.preferences.values_list("id", flat=True))
    selected_allergies_ids = list(profile.allergies.values_list("id", flat=True))

    return render(request, "vendor/select_preferences.html", {
        "preferences": preferences,
        "allergies": allergies,
        "selected_preferences_ids": [str(i) for i in selected_preferences_ids],
        "selected_allergies_ids": [str(i) for i in selected_allergies_ids],
    })


@login_required
def edit_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()
    allergies = Allergy.objects.all()   # 👈 agregamos alergias

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        selected_allergies = request.POST.getlist("allergies")

        profile.preferences.set(selected_prefs)
        profile.allergies.set(selected_allergies)
        profile.save()

        messages.success(request, "Configuración actualizada correctamente 🍕")
        return redirect("vendor:edit-preferences")

    # IDs seleccionados actualmente (para precargar chips)
    selected_preferences_ids = list(profile.preferences.values_list("id", flat=True))
    selected_allergies_ids = list(profile.allergies.values_list("id", flat=True))

    return render(request, "vendor/edit_preferences.html", {
        "preferences": preferences,
        "allergies": allergies,
        "selected_preferences_ids": [str(i) for i in selected_preferences_ids],
        "selected_allergies_ids": [str(i) for i in selected_allergies_ids],
    })


@login_required
def edit_offer(request, product_id):
    if not hasattr(request.user, "vendor"):
        return redirect("core:home")

    product = get_object_or_404(Product, id=product_id, vendor=request.user.vendor)

    # Si el producto tiene oferta → editar
    try:
        offer = product.offer
    except Offer.DoesNotExist:
        offer = None

    if request.method == "POST":
        form = OfferForm(request.POST, instance=offer)

        if form.is_valid():
            new_offer = form.save(commit=False)
            new_offer.product = product
            new_offer.save()

            messages.success(request, "Oferta actualizada correctamente 🎉")
            return redirect("vendor:profile")


        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = OfferForm(instance=offer)

    return render(request, "vendor/edit_offer.html", {
        "product": product,
        "form": form,
        "offer": offer,
    })


@login_required
def vendor_dashboard(request):
    return render(request, "vendor/vendor_profile.html")



@login_required
@vendor_required
def weekly_menu_edit(request):
    vendor = request.user.vendor  

    today = timezone.localdate()
    start_day = today
    end_day = today + datetime.timedelta(days=6)

    products = Product.objects.filter(vendor=vendor).order_by("title")

    menus = VendorWeeklyMenu.objects.filter(
        vendor=vendor,
        date__range=(start_day, end_day),
    )

    menus_by_date = {m.date: m for m in menus}

    weekday_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    days = []
    for i in range(7):
        d = start_day + datetime.timedelta(days=i)
        days.append({
            "date": d,
            "menu": menus_by_date.get(d),
            "weekday_label": weekday_labels[d.weekday()],
        })

    return render(request, "vendor/weekly_menu_edit.html", {
        "vendor": vendor,
        "days": days,
        "products": products,
        "monday": start_day,
        "sunday": end_day,
    })


@login_required
@vendor_required
@require_POST
def weekly_menu_assign(request):
    vendor = request.user.vendor

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"})

    product_id = data.get("product_id")
    date_str = data.get("date")

    if not product_id or not date_str:
        return JsonResponse({"ok": False, "error": "Datos incompletos"})

    # Validación fecha
    try:
        date_obj = datetime.date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Fecha inválida"})

    # Validación producto del vendor
    try:
        product = Product.objects.get(id=product_id, vendor=vendor)
    except Product.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Producto no encontrado para este vendedor"})

    VendorWeeklyMenu.objects.update_or_create(
        vendor=vendor,
        date=date_obj,
        defaults={"product": product},
    )

    # Imagen segura
    image_url = ""
    for img_field in ["thumbnail", "image"]:
        img = getattr(product, img_field, None)
        if img and hasattr(img, "url"):
            try:
                image_url = img.url
                break
            except:
                pass

    price_display = ""
    if product.price:
        price_display = f"${int(product.price):,}".replace(",", ".")

    return JsonResponse({
        "ok": True,
        "product_title": product.title,
        "product_price": price_display,
        "image_url": image_url,
        "date": str(date_obj),
    })

@vendor_required
@login_required


@login_required
@vendor_required
def weekly_menu_history(request):
    vendor = request.user.vendor

    today = timezone.localdate()

    # Leer filtros desde GET
    from_str = request.GET.get("from")
    to_str = request.GET.get("to")

    # Si no hay filtros → últimos 30 días
    if from_str and to_str:
        try:
            from_date = datetime.date.fromisoformat(from_str)
            to_date = datetime.date.fromisoformat(to_str)
        except ValueError:
            from_date = today - datetime.timedelta(days=29)
            to_date = today
    else:
        from_date = today - datetime.timedelta(days=29)
        to_date = today

    qs = (
        VendorWeeklyMenu.objects
        .filter(vendor=vendor, date__range=(from_date, to_date))
        .select_related("product")
        .order_by("-date")
    )

    paginator = Paginator(qs, 20)  # 20 días por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "vendor/weekly_menu_history.html", {
        "vendor": vendor,
        "page_obj": page_obj,
        "from_date": from_date,
        "to_date": to_date,
    })






@login_required
@vendor_required
@require_POST
def weekly_menu_clear(request):
    vendor = request.user.vendor

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"})

    date_str = data.get("date")
    if not date_str:
        return JsonResponse({"ok": False, "error": "Fecha no enviada"})

    try:
        date_obj = datetime.date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Fecha inválida"})

    VendorWeeklyMenu.objects.filter(vendor=vendor, date=date_obj).delete()

    return JsonResponse({"ok": True})

