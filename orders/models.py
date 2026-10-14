import uuid

from django.db import models


class Product(models.Model):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    price_cents = models.PositiveIntegerField()

    def __str__(self):
        return self.sku


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PAID = "paid"
        CANCELLED = "cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    customer_email = models.EmailField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"order {self.id}"

    def total_cents(self):
        return sum(line.quantity * line.unit_price_cents for line in self.lines.all())


class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_cents = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product_id}"
