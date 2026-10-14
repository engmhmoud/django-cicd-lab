import json

from django.test import TestCase

from .models import Order, Product
from .services import InvalidOrder, place_order


class PlaceOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(sku="MUG", name="Mug", price_cents=1200)
        Product.objects.create(sku="TEE", name="T-shirt", price_cents=2500)

    def test_total_uses_catalogue_prices(self):
        order = place_order("a@example.test", [{"sku": "MUG", "quantity": 2}, {"sku": "TEE", "quantity": 1}])
        self.assertEqual(order.total_cents(), 2 * 1200 + 2500)

    def test_unknown_sku_creates_nothing(self):
        with self.assertRaises(InvalidOrder):
            place_order("a@example.test", [{"sku": "MUG", "quantity": 1}, {"sku": "NOPE", "quantity": 1}])
        self.assertEqual(Order.objects.count(), 0)

    def test_empty_order_rejected(self):
        with self.assertRaises(InvalidOrder):
            place_order("a@example.test", [])


class EndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(sku="MUG", name="Mug", price_cents=1200)

    def test_healthz(self):
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})

    def test_readyz_checks_database(self):
        self.assertEqual(self.client.get("/readyz").json(), {"status": "ready"})

    def test_create_and_read_order(self):
        body = {"customer_email": "a@example.test", "items": [{"sku": "MUG", "quantity": 3}]}
        created = self.client.post("/api/orders", json.dumps(body), content_type="application/json")
        self.assertEqual(created.status_code, 201)
        detail = self.client.get(f"/api/orders/{created.json()['id']}")
        self.assertEqual(detail.json()["total_cents"], 3600)

    def test_bad_body_is_422(self):
        response = self.client.post("/api/orders", "{}", content_type="application/json")
        self.assertEqual(response.status_code, 422)
