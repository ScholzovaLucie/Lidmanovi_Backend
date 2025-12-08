from django.core.validators import MinValueValidator
from django.db import models

from guest.models import Guest
from room.models import Room


class ReservationStatus(models.TextChoices):
    NEW = "new", "New"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class Reservation(models.Model):
    check_in_date = models.DateField()
    check_out_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.NEW
    )

    num_adults = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    num_children = models.PositiveIntegerField(default=0)

    note_internal = models.TextField(blank=True)
    note_published = models.TextField(blank=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="EUR")

    primary_guest = models.ForeignKey(
        Guest,
        on_delete=models.PROTECT,
        related_name="reservations"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="reservations"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(check_in_date__lt=models.F("check_out_date")),
                name="check_reservation_dates"
            )
        ]
