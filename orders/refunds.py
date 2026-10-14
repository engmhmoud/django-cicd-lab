"""Refund policy: how much of a paid order can be refunded, and why not."""

from datetime import timedelta

from django.utils import timezone

FULL_REFUND_WINDOW = timedelta(days=14)
PARTIAL_REFUND_WINDOW = timedelta(days=30)
PARTIAL_REFUND_PERCENT = 50


class RefundNotAllowed(ValueError):
    pass


def refundable_cents(order, now=None):
    """Full refund within 14 days, 50 % up to 30 days, nothing after; only paid orders."""
    if order.status != order.Status.PAID:
        raise RefundNotAllowed(f"order is {order.status}, not paid")
    now = now or timezone.now()
    age = now - order.created_at
    total = order.total_cents()
    if age <= FULL_REFUND_WINDOW:
        return total
    if age <= PARTIAL_REFUND_WINDOW:
        return total * PARTIAL_REFUND_PERCENT // 100
    raise RefundNotAllowed(f"order is {age.days} days old; refunds end after {PARTIAL_REFUND_WINDOW.days} days")
