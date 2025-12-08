from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from rate_plan.models import RatePlan
from room_type.models import RoomType


class PriceRule(models.Model):
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)

    valid_from = models.DateField()
    valid_to = models.DateField()

    day_of_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    min_stay_nights = models.PositiveIntegerField(null=True, blank=True)
    max_stay_nights = models.PositiveIntegerField(null=True, blank=True)

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")
