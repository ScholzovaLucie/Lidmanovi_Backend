from django.db import models

from room_type.models import RoomType


class Package(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    base_nights = models.PositiveIntegerField()
    base_adults = models.PositiveIntegerField()
    base_children = models.PositiveIntegerField(default=0)

    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)

    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")

    is_external = models.BooleanField(default=False)
    external_provider_name = models.CharField(max_length=150, blank=True)
    external_provider_contact = models.CharField(max_length=255, blank=True)

    liability_disclaimer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
