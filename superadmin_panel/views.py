from datetime import timedelta
import json

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from .decorators import superadmin_required
from .forms import (
    OfferForm,
    VendorEditForm,
    VendorMessagingForm,
    CustomerEditForm
)
from .models import VendorMessageLog

from vendor.models import Vendor
from product.models import Product
from offers.models import Offer
from location.models import Provincia, Comuna


class ProductForm(forms.ModelForm):
    """Form para que el super admin edite productos de forma abstracta."""
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
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "preferences": forms.CheckboxSelectMultiple,
        }


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


@superadmin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    vendor_id = product.vendor_id

    if request.method == "POST":
        product.delete()
        messages.success(request, "🗑️ Producto eliminado correctamente.")
        return redirect("superadmin_panel:vendor_products", vendor_id=vendor_id)

    return redirect("superadmin_panel:vendor_products", vendor_id=vendor_id)


# =========================
# OFERTAS
# =========================

@superadmin_required
def offer_list(request):
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

    back_url = reverse("superadmin_panel:offer_list")

    if instance:
        product_from_url = instance.product
        back_url = reverse("superadmin_panel:vendor_products", args=[instance.product.vendor_id])
    elif product_id:
        product_from_url = get_object_or_404(Product, pk=product_id)
        back_url = reverse("superadmin_panel:vendor_products", args=[product_from_url.vendor_id])

    if request.method == "POST":
        form = OfferForm(request.POST, instance=instance)

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
        messages.success(request, "🗑️ Oferta registrada eliminada correctamente.")
        return redirect("superadmin_panel:offer_list")

    return render(
        request,
        "superadmin_panel/offer_confirm_delete.html",
        {"offer": offer},
    )


# =========================
# CONTROL DE PERFILES VENDORS
# =========================

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
    vendor.delete()

    messages.success(request, f"Vendedor «{name}» eliminado correctamente.")
    return redirect("superadmin_panel:vendor_list")


# =========================
# MENSAJERÍA MASIVA / SEGMENTACIÓN CHILE
# =========================

def _get_vendor_emails(qs):
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
            comuna_obj = form.cleaned_data.get("comuna")
            vendor = form.cleaned_data.get("vendor")

            subject = form.cleaned_data["subject"]
            body = form.cleaned_data["body"]
            attachment = form.cleaned_data.get("attachment")

            if target_type == "all":
                vendors_qs = Vendor.objects.all()
            elif target_type == "comuna":
                if not comuna_obj:
                    messages.error(request, "Debes seleccionar Región → Provincia → Comuna.")
                    return render(request, "superadmin_panel/vendor_messaging.html", {"form": form})
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

            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=None,
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

            comuna_str = comuna_obj.nombre if (target_type == "comuna" and comuna_obj) else None

            log = VendorMessageLog.objects.create(
                target_type=target_type,
                comuna=comuna_str,
                vendor_id=vendor.id if (target_type == "vendor" and vendor) else None,
                subject=subject,
                body=body,
                recipients_count=len(emails),
                sent_by=request.user if request.user.is_authenticated else None,
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


# =========================
# CONTROL DE COMPRADORES (CUSTOMERS)
# =========================

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