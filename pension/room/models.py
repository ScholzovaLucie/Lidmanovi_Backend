from django.db import models

from pension.reservation.enums import ReservationStatus


class Room(models.Model):
    name = models.CharField(max_length=50, unique=True, null=False)
    max_adults = models.PositiveIntegerField(default=1, null=False)
    max_children = models.PositiveIntegerField(default=0, null=False)
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(default=0, null=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def can_fit(self, adults, children):
        if adults > self.max_adults:
            return False
        if children > self.max_children:
            return False
        if adults + children > self.capacity:
            return False
        return True

    def is_available(self, from_date, to_date, adults, children):
        if not self.can_fit(adults, children):
            return False

        overlapping = self.reservations.filter(
            status__in=[
                ReservationStatus.NEW,
                ReservationStatus.CONFIRMED,
                ReservationStatus.PAYMENT_PENDING,
                ReservationStatus.PAYED,
            ],
            check_in_date__lt=to_date,
            check_out_date__gt=from_date,
        ).exists()

        return not overlapping
