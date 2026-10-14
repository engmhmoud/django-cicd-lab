from django.db import transaction

from .models import Order, OrderLine, Product


class InvalidOrder(ValueError):
    pass


def place_order(customer_email, items):
    """Create an order from [{"sku": ..., "quantity": ...}]; prices come from the catalogue, never the client."""
    if not items:
        raise InvalidOrder("an order needs at least one line")
    products = Product.objects.in_bulk([i["sku"] for i in items], field_name="sku")
    with transaction.atomic():
        order = Order.objects.create(customer_email=customer_email)
        for item in items:
            product = products.get(item["sku"])
            if product is None:
                raise InvalidOrder(f"unknown sku {item['sku']}")
            if item["quantity"] < 1:
                raise InvalidOrder("quantity must be at least 1")
            OrderLine.objects.create(
                order=order, product=product, quantity=item["quantity"], unit_price_cents=product.price_cents
            )
    return order
