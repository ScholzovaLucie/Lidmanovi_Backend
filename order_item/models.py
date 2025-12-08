from django.db import models

from order.models import Order
from package.models import Package


class OrderItemType(models.TextChoices):
    PACKAGE = "package", "Package"
    SERVICE = "service", "Service"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    item_type = models.CharField(max_length=20, choices=OrderItemType.choices)
    package = models.ForeignKey(Package, null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
