from datetime import timedelta
import json

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

from .decorators import superadmin_required
from .forms import (
    VendorWeeklyMenuForm,
    OfferForm,
    VendorEditForm,
    VendorMessagingForm,
    CustomerEditForm
)
from .models import VendorMessageLog

from vendor.models import Vendor, VendorWeeklyMenu
from product.models import Product, Ingredient, IngredientCategory
from offers.models import Offer
from location.models import Provincia, Comuna



class ProductForm(forms.ModelForm):
    """Form para que el super admin edite productos."""
    class Meta:
        model = Product
        fields = [
            "category",
            "vendor",
            "title",
            "description",
            "price",
            "image",
            "preferences",
            "ingredients",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "preferences": forms.CheckboxSelectMultiple,
            "ingredients": forms.CheckboxSelectMultiple,
        }


class IngredientCategoryForm(forms.ModelForm):
    class Meta:
        model = IngredientCategory
        fields = ["name", "ordering"]


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "category"]


# =========================
# VENDEDORES Y PRODUCTOS
# =========================

@superadmin_required
def vendor_list(request):
    vendors = Vendor.objects.select_related("created_by").all()
    return render(request, "superadmin_panel/vendor_list.html", {"vendors": vendors})


@superadmin_required
def vendor_products(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    products = Product.objects.filter(vendor=vendor).select_related("category")
    return render(
        request,
        "superadmin_panel/vendor_products.html",
        {"vendor": vendor, "products": products},
    )


@superadmin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Producto actualizado correctamente.")
            return redirect("superadmin_panel:vendor_products", vendor_id=product.vendor_id)
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "superadmin_panel/product_edit.html",
        {"form": form, "product": product},
    )


# @superadmin_required
# def product_delete(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     vendor_id = product.vendor_id

#     if request.method == "POST":
#         product.delete()
#         messages.success(request, "🗑️ Producto eliminado correctamente.")
#         return redirect("superadmin_panel:vendor_products", vendor_id=vendor_id)

#     return render(
#         request,
#         "superadmin_panel/product_confirm_delete.html",
#         {"product": product},
#     )


@superadmin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    vendor_id = product.vendor_id

    if request.method == "POST":
        product.delete()
        messages.success(request, "🗑️ Producto eliminado correctamente.")
        return redirect("superadmin_panel:vendor_products", vendor_id=vendor_id)

    # Si viene por GET, no mostramos otro template, solo volvemos a la vista de productos
    return redirect("superadmin_panel:vendor_products", vendor_id=vendor_id)




@superadmin_required
def ingredient_category_list(request):
    categories = IngredientCategory.objects.all()
    return render(
        request,
        "superadmin_panel/ingredient_category_list.html",
        {"categories": categories},
    )


@superadmin_required
def ingredient_category_edit(request, pk=None):
    if pk:
        category = get_object_or_404(IngredientCategory, pk=pk)
    else:
        category = None

    if request.method == "POST":
        form = IngredientCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Categoría guardada correctamente.")
            return redirect("superadmin_panel:ingredient_category_list")
    else:
        form = IngredientCategoryForm(instance=category)

    return render(
        request,
        "superadmin_panel/ingredient_category_edit.html",
        {"form": form, "category": category},
    )


@superadmin_required
def ingredient_category_delete(request, pk):
    category = get_object_or_404(IngredientCategory, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "🗑️ Categoría eliminada.")
        return redirect("superadmin_panel:ingredient_category_list")

    return render(
        request,
        "superadmin_panel/ingredient_category_confirm_delete.html",
        {"category": category},
    )


@superadmin_required
def ingredient_list(request):
    """
    Lista de ingredientes con filtro opcional por categoría.
    """
    category_id = request.GET.get("category")

    categories = IngredientCategory.objects.all().order_by("ordering", "name")
    ingredients = Ingredient.objects.select_related("category").all().order_by("name")

    if category_id:
        ingredients = ingredients.filter(category_id=category_id)

    return render(
        request,
        "superadmin_panel/ingredient_list.html",
        {
            "ingredients": ingredients,
            "categories": categories,
            "category_id": category_id,
        },
    )


@superadmin_required
def ingredient_edit(request, pk=None):
    if pk:
        ingredient = get_object_or_404(Ingredient, pk=pk)
    else:
        ingredient = None

    if request.method == "POST":
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Ingrediente guardado correctamente.")
            return redirect("superadmin_panel:ingredient_list")
    else:
        form = IngredientForm(instance=ingredient)

    return render(
        request,
        "superadmin_panel/ingredient_edit.html",
        {"form": form, "ingredient": ingredient},
    )


@superadmin_required
def ingredient_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)

    if request.method == "POST":
        ingredient.delete()
        messages.success(request, "🗑️ Ingrediente eliminado.")
        return redirect("superadmin_panel:ingredient_list")

    return render(
        request,
        "superadmin_panel/ingredient_confirm_delete.html",
        {"ingredient": ingredient},
    )


# =========================
# MENÚ SEMANAL
# =========================

@superadmin_required
def weekly_menu_list(request):
    vendor_id = request.GET.get("vendor")
    start = request.GET.get("start")
    end = request.GET.get("end")

    menus = VendorWeeklyMenu.objects.select_related("vendor", "product").all()

    if vendor_id:
        menus = menus.filter(vendor_id=vendor_id)

    if start:
        menus = menus.filter(date__gte=start)
    if end:
        menus = menus.filter(date__lte=end)

    menus = menus.order_by("date", "vendor__name")
    vendors = Vendor.objects.order_by("name")

    context = {
        "menus": menus,
        "vendors": vendors,
        "vendor_id": vendor_id,
        "start": start,
        "end": end,
    }
    return render(request, "superadmin_panel/weekly_menu_list.html", context)


@superadmin_required
def weekly_menu_edit(request, pk=None):
    if pk:
        instance = get_object_or_404(VendorWeeklyMenu, pk=pk)
    else:
        instance = None

    if request.method == "POST":
        form = VendorWeeklyMenuForm(request.POST, instance=instance)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "✅ Menú semanal guardado correctamente.")
                return redirect("superadmin_panel:weekly_menu_list")
            except Exception as e:
                messages.error(request, f"⚠️ Error al guardar menú: {e}")
    else:
        form = VendorWeeklyMenuForm(instance=instance)

    return render(
        request,
        "superadmin_panel/weekly_menu_edit.html",
        {"form": form, "menu": instance},
    )


@superadmin_required
def weekly_menu_delete(request, pk):
    menu = get_object_or_404(VendorWeeklyMenu, pk=pk)

    if request.method == "POST":
        menu.delete()
        messages.success(request, "🗑️ Registro del menú semanal eliminado.")
        return redirect("superadmin_panel:weekly_menu_list")

    return render(
        request,
        "superadmin_panel/weekly_menu_confirm_delete.html",
        {"menu": menu},
    )


# =========================
# OFERTAS
# =========================

@superadmin_required
def offer_list(request):
    """
    Lista todas las ofertas, con opción de filtrar por vendedor.
    """
    vendor_id = request.GET.get("vendor")

    offers = (
        Offer.objects
        .select_related("product", "product__vendor")
        .order_by("-created_at")
    )

    if vendor_id:
        offers = offers.filter(product__vendor_id=vendor_id)

    vendors = Vendor.objects.order_by("name")

    context = {
        "offers": offers,
        "vendors": vendors,
        "vendor_id": vendor_id,
    }
    return render(request, "superadmin_panel/offer_list.html", context)



@superadmin_required
def offer_edit(request, pk=None):
    instance = get_object_or_404(Offer, pk=pk) if pk else None

    product_id = request.GET.get("product")
    product_from_url = None

    # Definir back_url
    back_url = reverse("superadmin_panel:offer_list")

    if instance:
        product_from_url = instance.product
        back_url = reverse("superadmin_panel:vendor_products", args=[instance.product.vendor_id])
    elif product_id:
        product_from_url = get_object_or_404(Product, pk=product_id)
        back_url = reverse("superadmin_panel:vendor_products", args=[product_from_url.vendor_id])

    if request.method == "POST":
        form = OfferForm(request.POST, instance=instance)

        # fijar producto si viene por URL o si es edición
        if product_from_url:
            form.instance.product = product_from_url

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Oferta guardada correctamente.")
            return redirect(back_url)
    else:
        initial = {}
        if not instance and product_from_url:
            initial["product"] = product_from_url
        form = OfferForm(instance=instance, initial=initial)

    # OCULTAR CAMPO PRODUCTO SI YA VIENE DEFINIDO
    hide_product_field = bool(product_from_url)

    return render(
        request,
        "superadmin_panel/offer_edit.html",
        {
            "form": form,
            "offer": instance,
            "product_from_url": product_from_url,
            "hide_product_field": hide_product_field,
            "back_url": back_url,
        },
    )



@superadmin_required
def offer_delete(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    if request.method == "POST":
        offer.delete()
        messages.success(request, "🗑️ Oferta eliminada correctamente.")
        return redirect("superadmin_panel:offer_list")

    return render(
        request,
        "superadmin_panel/offer_confirm_delete.html",
        {"offer": offer},
    )

@superadmin_required
def weekly_menu_admin(request):
    """
    Vista visual de menú semanal para Súper Admin:
    1) Selecciona vendedor.
    2) Drag & drop de pizzas para cada día, igual que el panel del vendedor.
    """
    vendors = Vendor.objects.order_by("name")
    vendor_id = request.GET.get("vendor")

    selected_vendor = None
    products = []
    days = []
    monday = sunday = None

    if vendor_id:
        selected_vendor = get_object_or_404(Vendor, pk=vendor_id)

        # Productos del vendedor
        products = Product.objects.filter(vendor=selected_vendor).order_by("title")

        # Semana actual (lunes a domingo)
        today = timezone.localdate()
        monday = today
        sunday = today + timedelta(days=6)

        # Menús existentes para esa semana
        menus = (
            VendorWeeklyMenu.objects
            .filter(vendor=selected_vendor, date__range=[monday, sunday])
            .select_related("product")
        )
        menus_by_date = {m.date: m for m in menus}

        weekday_labels = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        days = []
        for offset in range(7):
            day_date = today + timedelta(days=offset)
            menu = menus_by_date.get(day_date)
            days.append({
                "date": day_date,
                "weekday_label": weekday_labels[day_date.weekday()],
                "menu": menu,
            })


    context = {
        "vendors": vendors,
        "selected_vendor": selected_vendor,
        "products": products,
        "days": days,
        "monday": monday,
        "sunday": sunday,
    }
    return render(request, "superadmin_panel/weekly_menu_edit.html", context)
@superadmin_required
@require_POST
def weekly_menu_assign_admin(request):
    """
    Asigna (o reemplaza) un producto para un día específico de un vendedor,
    usado por el drag & drop del Súper Admin.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    vendor_id = data.get("vendor_id")
    product_id = data.get("product_id")
    date_str = data.get("date")

    if not (vendor_id and product_id and date_str):
        return JsonResponse({"ok": False, "error": "Datos incompletos"}, status=400)

    date = parse_date(date_str)
    if not date:
        return JsonResponse({"ok": False, "error": "Fecha inválida"}, status=400)

    vendor = get_object_or_404(Vendor, pk=vendor_id)
    product = get_object_or_404(Product, pk=product_id, vendor=vendor)

    menu, created = VendorWeeklyMenu.objects.update_or_create(
        vendor=vendor,
        date=date,
        defaults={"product": product},
    )

    # Imagen (thumb si existe)
    image_url = ""
    if product.thumbnail:
        image_url = product.thumbnail.url
    elif product.image:
        image_url = product.image.url

    price_str = f"${product.price:,}".replace(",", ".") if product.price else "Precio no definido"

    return JsonResponse({
        "ok": True,
        "product_title": product.title,
        "product_price": price_str,
        "image_url": image_url,
    })


@superadmin_required
@require_POST
def weekly_menu_clear_admin(request):
    """
    Borra el producto asignado a un día específico para un vendedor.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    vendor_id = data.get("vendor_id")
    date_str = data.get("date")

    if not (vendor_id and date_str):
        return JsonResponse({"ok": False, "error": "Datos incompletos"}, status=400)

    date = parse_date(date_str)
    if not date:
        return JsonResponse({"ok": False, "error": "Fecha inválida"}, status=400)

    vendor = get_object_or_404(Vendor, pk=vendor_id)

    VendorWeeklyMenu.objects.filter(vendor=vendor, date=date).delete()

    return JsonResponse({"ok": True})



@superadmin_required
def vendor_edit(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)

    if request.method == "POST":
        form = VendorEditForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendedor actualizado correctamente.")
            return redirect("superadmin_panel:vendor_list")
    else:
        form = VendorEditForm(instance=vendor)

    return render(request, "superadmin_panel/vendor_edit.html", {
        "form": form,
        "vendor": vendor,
    })

@require_POST
@superadmin_required
def vendor_delete(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    name = vendor.name

    # Opcional: también borrar el usuario asociado
    user = vendor.created_by

    vendor.delete()
    # Si quieres borrar también al user (solo si ese user no se usa en otro lado):
    # user.delete()

    messages.success(request, f"Vendedor «{name}» eliminado correctamente.")
    return redirect("superadmin_panel:vendor_list")

@superadmin_required
def ingredient_manage(request):
    # Datos base
    categories = IngredientCategory.objects.order_by("name")
    ingredients = (
        Ingredient.objects.select_related("category")
        .order_by("category__name", "name")
    )

    # Forms "vacíos" por defecto (para el GET o para re-renderizar con errores)
    cat_form = IngredientCategoryForm()
    ing_form = IngredientForm()

    if request.method == "POST":
        action = request.POST.get("action")

        # -------------------------
        # 1) CREAR CATEGORÍA
        # -------------------------
        if action == "create_category":
            cat_form = IngredientCategoryForm(request.POST)
            if cat_form.is_valid():
                cat_form.save()
                messages.success(request, "Categoría creada correctamente ✅.")
                return redirect("superadmin_panel:ingredient_manage")
            else:
                messages.error(request, "Revisa el formulario de categoría.")

        # -------------------------
        # 2) EDITAR / ELIMINAR CATEGORÍA
        # -------------------------
        elif action == "category_modify":
            category_id = request.POST.get("category_id")
            submit_type = request.POST.get("submit_type")
            category = get_object_or_404(IngredientCategory, pk=category_id)

            if submit_type == "delete":
                nombre = category.name
                category.delete()
                messages.success(
                    request,
                    f"Categoría «{nombre}» eliminada. Los ingredientes quedan sin categoría."
                )
                return redirect("superadmin_panel:ingredient_manage")

            elif submit_type == "update":
                # Solo actualizamos el nombre
                new_name = request.POST.get("name", "").strip()
                if not new_name:
                    messages.error(request, "El nombre de la categoría no puede estar vacío.")
                else:
                    category.name = new_name
                    try:
                        category.full_clean()  # valida unique, longitudes, etc.
                        category.save()
                        messages.success(
                            request,
                            f"Categoría actualizada a «{category.name}» ✅."
                        )
                        return redirect("superadmin_panel:ingredient_manage")
                    except ValidationError as e:
                        messages.error(
                            request,
                            "Error al actualizar la categoría: "
                            + "; ".join(e.messages)
                        )

 
        elif action == "create_ingredient":
            ing_form = IngredientForm(request.POST)
            if ing_form.is_valid():
                ing_form.save()
                messages.success(request, "Ingrediente agregado correctamente ✅.")
                return redirect("superadmin_panel:ingredient_manage")
            else:
                messages.error(request, "Revisa el formulario de ingredientes.")


        elif action == "ingredient_modify":
            ingredient_id = request.POST.get("ingredient_id")
            submit_type = request.POST.get("submit_type")
            ingredient = get_object_or_404(Ingredient, pk=ingredient_id)

            if submit_type == "delete":
                nombre = ingredient.name
                ingredient.delete()
                messages.success(
                    request,
                    f"Ingrediente «{nombre}» eliminado correctamente ✅."
                )
                return redirect("superadmin_panel:ingredient_manage")

            elif submit_type == "update":
                new_name = request.POST.get("name", "").strip()
                if not new_name:
                    messages.error(request, "El nombre del ingrediente no puede estar vacío.")
                else:
                    ingredient.name = new_name
                    try:
                        ingredient.full_clean()
                        ingredient.save()
                        messages.success(
                            request,
                            f"Ingrediente actualiz ado a «{ingredient.name}» ✅."
                        )
                        return redirect("superadmin_panel:ingredient_manage")
                    except ValidationError as e:
                        messages.error(
                            request,
                            "Error al actualizar el ingrediente: "
                            + "; ".join(e.messages)
                        )

    context = {
        "categories": categories,
        "ingredients": ingredients,
        "cat_form": cat_form,
        "ing_form": ing_form,
    }
    return render(request, "superadmin_panel/ingredient_manage.html", context)





def _get_vendor_emails(qs):
    """Emails reales del vendedor: Vendor.created_by.email"""
    emails = set()
    qs = qs.select_related("created_by")

    for v in qs:
        email = getattr(v.created_by, "email", None)
        if email:
            emails.add(email.strip().lower())

    return list(emails)


def vendor_messaging(request):
    if request.method == "POST":
        form = VendorMessagingForm(request.POST, request.FILES)
        if form.is_valid():
            target_type = form.cleaned_data["target_type"]

            # Ahora comuna es objeto Comuna (ModelChoiceField)
            comuna_obj = form.cleaned_data.get("comuna")
            vendor = form.cleaned_data.get("vendor")

            subject = form.cleaned_data["subject"]
            body = form.cleaned_data["body"]
            attachment = form.cleaned_data.get("attachment")

            # 1) Resolver destinatarios
            if target_type == "all":
                vendors_qs = Vendor.objects.all()

            elif target_type == "comuna":
                if not comuna_obj:
                    messages.error(request, "Debes seleccionar Región → Provincia → Comuna.")
                    return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})

                # ✅ filtro correcto según tu modelo
                vendors_qs = Vendor.objects.filter(created_by__profile__comuna=comuna_obj)

            elif target_type == "vendor":
                if not vendor:
                    messages.error(request, "Debes seleccionar un vendedor.")
                    return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})

                vendors_qs = Vendor.objects.filter(id=vendor.id)

            else:
                messages.error(request, "Tipo de destinatario inválido.")
                return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})

            emails = _get_vendor_emails(vendors_qs)

            if not emails:
                messages.error(request, "No se encontraron correos para el filtro seleccionado.")
                return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})

            # 2) Enviar correo (BCC para no exponer correos)
            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=None,  # DEFAULT_FROM_EMAIL en settings
                to=[],
                bcc=emails,
                reply_to=[request.user.email] if getattr(request.user, "email", None) else None,
            )

            attachment_bytes = None
            attachment_name = None
            attachment_type = None

            if attachment:
                attachment_name = attachment.name
                attachment_type = attachment.content_type
                attachment_bytes = attachment.read()
                msg.attach(attachment_name, attachment_bytes, attachment_type)

            msg.send(fail_silently=False)

            # 3) Guardar historial (comuna ES TEXTO)
            comuna_str = comuna_obj.nombre if (target_type == "comuna" and comuna_obj) else None

            log = VendorMessageLog.objects.create(
                target_type=target_type,
                comuna=comuna_str,
                vendor_id=vendor.id if (target_type == "vendor" and vendor) else None,
                subject=subject,
                body=body,
                recipients_count=len(emails),
                sent_by=request.user if request.user.is_authenticated else None,
                # created_at se setea solo por auto_now_add=True
            )

            if attachment_bytes is not None:
                log.attachment.save(attachment_name, ContentFile(attachment_bytes), save=True)

            messages.success(request, f"Correo enviado a {len(emails)} vendedor(es).")
            return redirect("superadmin_panel:vendor_messaging_history")

    else:
        form = VendorMessagingForm()

    return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})


def vendor_messaging_history(request):
    qs = VendorMessageLog.objects.all().order_by("-created_at")
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "superadmin_panel/vendor_messaging_history.html", {"page": page})


def api_provincias(request):
    region_id = request.GET.get("region_id")
    if not region_id:
        return JsonResponse({"results": []})

    provincias = Provincia.objects.filter(region_id=region_id).order_by("nombre")
    data = [{"id": p.id, "nombre": p.nombre} for p in provincias]
    return JsonResponse({"results": data})


def api_comunas(request):
    provincia_id = request.GET.get("provincia_id")
    if not provincia_id:
        return JsonResponse({"results": []})

    comunas = Comuna.objects.filter(provincia_id=provincia_id).order_by("nombre")
    data = [{"id": c.id, "nombre": c.nombre} for c in comunas]
    return JsonResponse({"results": data})



@superadmin_required
def customer_list(request):
    customers = User.objects.filter(vendor__isnull=True).order_by("username")
    return render(request, "superadmin_panel/customer_list.html", {"customers": customers})


@superadmin_required
def customer_edit(request, customer_id):
    customer = get_object_or_404(User, id=customer_id, vendor__isnull=True)

    if request.method == "POST":
        form = CustomerEditForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Comprador actualizado correctamente.")
            return redirect("superadmin_panel:customer_list")
    else:
        form = CustomerEditForm(instance=customer)

    return render(request, "superadmin_panel/customer_edit.html", {"form": form, "customer": customer})



@require_POST
@superadmin_required
def customer_delete(request, customer_id):
    customer = get_object_or_404(User, id=customer_id, vendor__isnull=True)

    username = customer.username
    customer.delete()

    messages.success(request, f"Comprador «{username}» eliminado correctamente.")
    return redirect("superadmin_panel:customer_list")