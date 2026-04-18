from django.db import models

from pension.reservation.enums import ReservationStatus


class Room(models.Model):
    name = models.CharField(max_length=50, unique=True, null=False)
    name_i18n = models.JSONField(default=dict, blank=True)
    max_adults = models.PositiveIntegerField(default=1, null=False)
    max_children = models.PositiveIntegerField(default=0, null=False)
    capacity = models.PositiveIntegerField(default=1, null=False)
    description = models.TextField(blank=True)
    description_i18n = models.JSONField(default=dict, blank=True)
    price_for_adult = models.PositiveIntegerField(default=0, null=False)
    price_for_children = models.PositiveIntegerField(default=0, null=False)
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

    def calculate_price_per_day(self, adults, children):
        price = 0
        if not self.can_fit(adults, children):
            raise ValueError("Room does not fit the requested number of guests.")

        if adults > 0 :
            price += adults * self.price_for_adult

        if children > 0:
            price += children * self.price_for_children

        return price

    def is_free(self, from_date, to_date):
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

    def is_available(self, from_date, to_date, adults, children):
        if not self.can_fit(adults, children):
            return False
        return self.is_free(from_date, to_date)
