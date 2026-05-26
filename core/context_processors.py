from product.views import get_active_comuna

def comuna_context(request):
    try:
        comuna = get_active_comuna(request)
    except Exception:
        comuna = None

    return {
        "comuna_activa": comuna
    }


def price_helpers(request):
    return {
        "final_price": lambda p: p.final_price,
        "normal_price": lambda p: p.price,
    }


