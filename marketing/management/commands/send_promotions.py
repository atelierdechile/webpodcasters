from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from vendor.models import Vendor
from product.models import Product


class Command(BaseCommand):
    help = "Envía promociones reales filtradas por comuna, preferencias y ofertas activas"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Excluir vendedores
        vendedores_ids = Vendor.objects.values_list("created_by_id", flat=True)

        usuarios = User.objects.exclude(
            id__in=vendedores_ids
        ).exclude(email="").exclude(email__isnull=True)

        now = timezone.now()
        enviados = 0

        for user in usuarios:

            profile = user.profile
            comuna = profile.comuna
            prefs = profile.preferences.all()

            producto = None

            # =============================================================
            # 1️⃣ Buscar ofertas activas SOLO en la comuna del usuario
            # =============================================================
            ofertas_comuna = Product.objects.filter(
                vendor__created_by__profile__comuna=comuna,
                offer__is_active=True,
                offer__start_date__lte=now,
                offer__end_date__gte=now,
            ).distinct()

            # Si el usuario tiene preferencias → filtrar por preferencias
            if prefs.exists():
                ofertas_pref = ofertas_comuna.filter(preferences__in=prefs).distinct()

                if ofertas_pref.exists():
                    producto = ofertas_pref.first()
                else:
                    producto = None  # hay ofertas pero NO cumplen preferencias

            else:
                # Usuario SIN preferencias → cualquier oferta de la comuna sirve
                if ofertas_comuna.exists():
                    producto = ofertas_comuna.first()

            # =============================================================
            # 2️⃣ SI NO HAY UNA OFERTA VÁLIDA → correo genérico
            # =============================================================
            if not producto:
                asunto = "🍕 Ofertas del día — Descubre nuestras mejores pizzas"
                html = render_to_string(
                    "marketing/oferta_generica.html",
                    {
                        "user": user,
                        "site_url": "https://nicolasbriceno.pythonanywhere.com",
                    }
                )
            else:
                # =========================================================
                # Plantilla de oferta real
                # =========================================================
                offer = producto.active_offer

                if offer.is_2x1:
                    tipo = "2x1"
                elif offer.discount_percentage:
                    tipo = "porcentaje"
                elif offer.discount_price:
                    tipo = "precio"
                else:
                    tipo = "precio"

                asunto = f"🔥 Oferta especial en {comuna}: {producto.title}"

                html = render_to_string(
                    "marketing/oferta_comuna.html",
                    {
                        "user": user,
                        "producto": producto,
                        "comuna": comuna,
                        "preferences": prefs,
                        "site_url": "https://nicolasbriceno.pythonanywhere.com",
                        "image_url": f"https://nicolasbriceno.pythonanywhere.com{producto.image.url}" if producto.image else "",
                        "tipo_oferta": tipo,
                        "price_original": producto.price,
                        "price_final": producto.get_final_price(),
                        "es_2x1": offer.is_2x1,
                        "porcentaje": producto.get_offer_percentage(),
                    }
                )

            # =============================================================
            # ENVIAR EMAIL
            # =============================================================
            msg = EmailMultiAlternatives(
                subject=asunto,
                body="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            enviados += 1

        self.stdout.write(self.style.SUCCESS(f"✔ Correos enviados: {enviados}"))
