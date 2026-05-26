import re
from product.models import Product
from offers.models import Offer

# Expresión para detectar caracteres problemáticos
pattern = re.compile(r"[\r\n\t\xa0*~_`]+")

def check_products():
    print("\n🔍 Revisando productos en busca de errores...\n")
    found = False

    for p in Product.objects.all():
        issues = []

        # --- TITULO ---
        if not p.title or pattern.search(p.title):
            issues.append(f"⚠️ Título inválido o con caracteres sospechosos: {repr(p.title)}")

        # --- SLUG ---
        if not p.slug:
            issues.append("⚠️ Slug vacío")
        elif Product.objects.filter(slug=p.slug).exclude(id=p.id).exists():
            issues.append(f"⚠️ Slug duplicado: '{p.slug}'")

        # --- PRECIO ---
        try:
            precio = str(p.price)
            if pattern.search(precio) or p.price <= 0:
                issues.append(f"💰 Precio inválido o negativo: {repr(precio)}")
        except Exception:
            issues.append("💰 Precio no legible")

        # --- DESCRIPCIÓN ---
        if p.description:
            if pattern.search(p.description):
                issues.append(f"📝 Descripción con caracteres sospechosos para '{p.title}'")

        # --- IMAGEN ---
        try:
            url = p.image.url
            if not url:
                issues.append("🖼 Imagen vacía")
            elif "http://" in url:
                issues.append("🖼 Imagen insegura (HTTP)")
        except Exception:
            issues.append("🖼 Sin imagen asociada")

        # --- PREFERENCIAS (opcional) ---
        if p.preferences.count() == 0:
            issues.append("🌱 Sin preferencias (opcional)")

        # --- OFERTA ---
        try:
            if p.active_offer:
                offer = p.active_offer

                if offer.discount_percentage and not (1 <= offer.discount_percentage <= 90):
                    issues.append(f"🔥 % descuento fuera de rango: {offer.discount_percentage}%")

                if offer.discount_price and offer.discount_price >= p.price:
                    issues.append(
                        f"🔥 Precio de oferta ({offer.discount_price}) es mayor o igual al normal ({p.price})"
                    )

                if offer.start_date >= offer.end_date:
                    issues.append("🔥 Fechas de oferta inválidas (inicio >= fin)")

        except Offer.DoesNotExist:
            pass  # No hay oferta → OK

        # --- MOSTRAR RESULTADOS ---
        if issues:
            found = True
            print(f"🔸 Producto ID {p.id} — {p.title}")
            for err in issues:
                print("   ", err)
            print()

    if not found:
        print("✅ Todos los productos están limpios y seguros.")

    print("\n✔ Revisión completa.\n")
