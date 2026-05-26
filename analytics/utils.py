from .models import UserActionLog
from django.db import DatabaseError

def classify_section(page: str, action: str) -> str:
    """Detecta la sección a partir de la ruta o acción."""
    page = (page or "").lower()
    action = (action or "").lower()

    if "product" in page:
        return "productos"
    elif "category" in page:
        return "categorias"
    elif "cart" in page:
        return "carrito"
    elif "checkout" in page:
        return "checkout"
    elif "error" in action:
        return "errores"
    elif "manychat" in page or "bot" in page or "whatsapp" in page:
        return "bot"
    else:
        return "otros"


def log_event(request, action, page="", product_id=None, extra_data=None):
    """
    Registra un evento incluyendo información del sistema de OFERTAS.
    (SIN el campo status)
    """
    offer_info = {}

    # Si el evento está relacionado a un producto, capturar oferta
    if product_id:
        try:
            from product.models import Product
            product = Product.objects.get(id=product_id)

            if product.active_offer:
                offer = product.active_offer
                offer_info = {
                    "offer_active": True,
                    "offer_type": (
                        "percentage" if offer.discount_percentage else
                        "fixed" if offer.discount_price else
                        "2x1" if offer.is_2x1 else "unknown"
                    ),
                    "original_price": product.price,
                    "final_price": product.final_price,
                    "discount_percentage": offer.discount_percentage or 0,
                    "discount_price": offer.discount_price or None,
                }
            else:
                offer_info = {
                    "offer_active": False,
                    "original_price": product.price,
                    "final_price": product.price
                }

        except Exception as e:
            offer_info = {"offer_error": str(e)}

    # Mezclar con extra_data
    merged_extra = {**offer_info, **(extra_data or {})}

    # Crear log sin status
    UserActionLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        user_name=request.user.username if request.user.is_authenticated else "Anon",
        action=action,
        page=page,
        product_id=product_id,
        extra_data=merged_extra,
        section=classify_section(page, action)
    )
