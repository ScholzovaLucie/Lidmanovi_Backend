from django.db import models


class ReservationItem(models.Model):
    name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
