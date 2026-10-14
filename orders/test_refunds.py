from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Order, Product
from .refunds import RefundNotAllowed, refundable_cents
from .services import place_order


class RefundPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(sku="MUG", name="Mug", price_cents=1200)

    def paid_order(self, days_old):
        order = place_order("a@example.test", [{"sku": "MUG", "quantity": 2}])
        order.status = Order.Status.PAID
        order.save()
        return order, order.created_at + timedelta(days=days_old)

    def test_full_refund_within_14_days(self):
        order, now = self.paid_order(days_old=14)
        self.assertEqual(refundable_cents(order, now=now), 2400)

    def test_half_refund_up_to_30_days(self):
        order, now = self.paid_order(days_old=30)
        self.assertEqual(refundable_cents(order, now=now), 1200)

    def test_no_refund_after_30_days(self):
        order, now = self.paid_order(days_old=31)
        with self.assertRaisesMessage(RefundNotAllowed, "31 days old"):
            refundable_cents(order, now=now)

    def test_only_paid_orders(self):
        order = place_order("a@example.test", [{"sku": "MUG", "quantity": 1}])
        with self.assertRaisesMessage(RefundNotAllowed, "pending"):
            refundable_cents(order, now=timezone.now())
