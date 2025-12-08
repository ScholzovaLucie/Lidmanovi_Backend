from django.db import models

from reservation.models import Reservation


class OrderStatus(models.TextChoices):
    NEW = "new", "New"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="EUR")

    created_at = models.DateTimeField(auto_now_add=True)
    note_internal = models.TextField(blank=True)
