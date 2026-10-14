"""Lab 3 only: a heavier, DB-bound suite to compare serial and parallel test runs.

Not named test*.py, so `manage.py test` (and ci.yml) never collects it; run it explicitly:
    python manage.py test orders.heavy_checks --parallel 1
    python manage.py test orders.heavy_checks --parallel auto
"""

from django.test import TestCase

from .models import Order, Product
from .services import place_order

ORDERS_PER_TEST = 40


class _HeavyBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.bulk_create(
            [Product(sku=f"SKU{i}", name=f"Product {i}", price_cents=100 + i) for i in range(50)]
        )

    def _place_many(self, seed):
        for n in range(ORDERS_PER_TEST):
            items = [{"sku": f"SKU{(seed + n + k) % 50}", "quantity": 1 + k} for k in range(3)]
            place_order(f"c{n}@example.test", items)
        self.assertEqual(Order.objects.count(), ORDERS_PER_TEST)


def _make_case(index):
    def make_test(seed):
        return lambda self: self._place_many(seed)

    attrs = {f"test_batch_{t}": make_test(index * 10 + t) for t in range(5)}
    return type(f"HeavyCase{index:02d}", (_HeavyBase,), attrs)


for _i in range(24):
    globals()[f"HeavyCase{_i:02d}"] = _make_case(_i)
