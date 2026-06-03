from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProductForm
from .models import Vendor, Profile, Preference 
from product.models import Product
from django.contrib import messages
from order.models import Order

# --- REGISTRO DE CLIENTE ---
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


# --- REGISTRO DE VENDEDOR ---
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

            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')
            else:
                return redirect('core:home')
    else:
        form = SignUpForm()

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


# --- PANEL DE ADMINISTRACIÓN DEL CREADOR (VENDOR) ---
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

    return render(request, 'vendor/vendor_profile.html', context)


# --- AGREGAR PRODUCTO O SERVICIO ---
@login_required
def add_product(request):
    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor  
            product.save()  

            # Guarda solo las preferencias/intereses (M2M)
            form.save_m2m()
            return redirect('vendor:profile')
    else:
        form = ProductForm()

    return render(request, 'vendor/add_product.html', {'form': form})


# --- ELIMINAR PRODUCTO ---
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    return redirect('vendor:profile')


# --- EDITAR INFORMACIÓN DEL CREADOR ---
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


# --- LISTA Y PERFILES ---
def vendors(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendors.html', {'vendors': vendors})


def vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    return render(request, 'vendor/vendor.html', {'vendor': vendor})


# --- VISTA GLOBAL DEL PERFIL (CLIENTE / PROVEEDOR) ---
@login_required
def profile_view(request):
    user = request.user

    if hasattr(user, "vendor"):
        vendor = user.vendor
        products = vendor.products.all()
        items = vendor.items.select_related("order", "product").all()
        orders = Order.objects.filter(items__vendor=vendor).distinct().order_by('-id')

        return render(request, "vendor/vendor_profile.html", {
            "vendor": vendor,
            "products": products,
            "orders": orders,
            "items": items,
        })

    # Perfil del Cliente/Usuario normal (Limpio de alergias)
    profile = user.profile
    preferences = Preference.objects.all()
    selected_ids = list(profile.preferences.values_list("id", flat=True))

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        profile.preferences.set(selected_prefs)
        profile.save()

        messages.success(request, "Intereses actualizados correctamente 🎉")
        return redirect("vendor:profile")

    return render(request, "vendor/customer_profile.html", {
        "profile": profile,
        "username": user.username,
        "email": user.email,
        "preferences": preferences,
        "selected_ids": selected_ids,
    })


# --- ONBOARDING DE PREFERENCIAS ---
@login_required
def select_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()

    if profile.preferences.exists():
        return redirect('core:home')

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        profile.preferences.set(selected_prefs)
        profile.save()
        return redirect('core:home')

    selected_preferences_ids = list(profile.preferences.values_list("id", flat=True))

    return render(request, "vendor/select_preferences.html", {
        "preferences": preferences,
        "selected_preferences_ids": [str(i) for i in selected_preferences_ids],
    })


# --- EDITAR PREFERENCIAS DESDE LA CONFIGURACIÓN ---
@login_required
def edit_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()

    if request.method == "POST":
        selected_prefs = request.POST.getlist("preferences")
        profile.preferences.set(selected_prefs)
        profile.save()

        messages.success(request, "Configuración actualizada correctamente 🎉")
        return redirect("vendor:edit-preferences")

    selected_preferences_ids = list(profile.preferences.values_list("id", flat=True))

    return render(request, "vendor/edit_preferences.html", {
        "preferences": preferences,
        "selected_preferences_ids": [str(i) for i in selected_preferences_ids],
    })

@login_required
def vendor_dashboard(request):
    return render(request, "vendor/vendor_profile.html")

@login_required
def edit_offer(request, product_id):
    if not hasattr(request.user, "vendor"):
        return redirect("core:home")

    product = get_object_or_404(Product, id=product_id, vendor=request.user.vendor)

    try:
        offer = product.offer
    except Exception: 
        offer = None

    if request.method == "POST":
        from offers.forms import OfferForm 
        form = OfferForm(request.POST, instance=offer)

        if form.is_valid():
            new_offer = form.save(commit=False)
            new_offer.product = product
            new_offer.save()

            messages.success(request, "Oferta actualizada correctamente 🎉")
            return redirect("vendor:profile")
    else:
        from offers.forms import OfferForm
        form = OfferForm(instance=offer)

    return render(request, "vendor/edit_offer.html", {
        "product": product,
        "form": form,
        "offer": offer,
    })