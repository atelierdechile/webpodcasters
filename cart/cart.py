from django.conf import settings
from product.models import Product

class Cart(object):

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    # =========================================================
    # ITERADOR DEL CARRITO (OFERTAS + 2x1 LISTO)
    # =========================================================
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(pk__in=product_ids)
        product_map = {str(p.id): p for p in products}

        for pid, item in self.cart.items():
            product = product_map.get(pid)
            if not product:
                continue

            quantity = item["quantity"]
            unit_price = product.get_final_price()

            # 🔥 Lógica 2x1
            if product.active_offer and product.active_offer.is_2x1:
                effective_qty = (quantity // 2) + (quantity % 2)
                total_price = effective_qty * unit_price
                is_two_for_one = True
            else:
                effective_qty = quantity
                total_price = quantity * unit_price
                is_two_for_one = False

            yield {
                "id": product.id,
                "product": product,
                "quantity": quantity,
                "effective_qty": effective_qty,
                "unit_price": unit_price,
                "is_two_for_one": is_two_for_one,
                "total_price": total_price,
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    # =========================================================
    # AGREGAR AL CARRITO
    # =========================================================
    def add(self, product_id, quantity=1, update_quantity=False):
        product_id = str(product_id)

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "id": product_id}

        if update_quantity:
            self.cart[product_id]["quantity"] = int(quantity)
        else:
            self.cart[product_id]["quantity"] += int(quantity)

        if self.cart[product_id]["quantity"] <= 0:
            self.remove(product_id)

        self.save()

    # =========================================================
    # ELIMINAR ÍTEM
    # =========================================================
    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    # =========================================================
    # GUARDAR SESIÓN
    # =========================================================
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    # =========================================================
    # LIMPIAR CARRITO
    # =========================================================
    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    # =========================================================
    # TOTAL DEL CARRITO (OFERTA + 2x1)
    # =========================================================
    def get_total_cost(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(pk__in=product_ids)
        product_map = {str(p.id): p for p in products}

        total = 0
        for pid, item in self.cart.items():
            product = product_map.get(pid)
            if not product:
                continue

            quantity = item["quantity"]
            unit_price = product.get_final_price()

            # 2x1
            if product.active_offer and product.active_offer.is_2x1:
                effective_qty = (quantity // 2) + (quantity % 2)
                total += effective_qty * unit_price
            else:
                total += quantity * unit_price

        return total
