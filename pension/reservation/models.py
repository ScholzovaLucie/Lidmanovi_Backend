from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from pension.guest.models import Guest
from pension.reservation.enums import ReservationStatus
from pension.room.models import Room


STATSU_MAP_TO_MAIL = {
    ReservationStatus.NEW: "reservation_received",
    ReservationStatus.CONFIRMED: "reservation_approved",
    ReservationStatus.CANCELLED: "reservation_rejected",
    ReservationStatus.PAYED: "reservation_payd",
    ReservationStatus.DONE: "reservation_done",
}


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

    note = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="CZK")

    primary_guest = models.ForeignKey(
        Guest,
        on_delete=models.PROTECT,
        related_name="reservations",
        help_text="The primary guest who will receive the reservation",
    )

    rooms = models.ManyToManyField(
        Room,
        null=True,
        blank=True,
        related_name="reservations"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(check_in_date__lt=models.F("check_out_date")),
                name="check_reservation_dates"
            )
        ]

    def validate_rooms(self, rooms):
        """
        rooms: [
            {
                "id",
                "num_adults",
                "num_children",
            }
        ]

        """
        if not rooms:
            raise ValidationError("At least one room must be selected.")

        total_people = self.num_adults + self.num_children

        # 1️⃣ kapacita
        for room_data in rooms:
            try:
                room = Room.objects.get(id=room_data['id'])
            except Room.DoesNotExist:
                raise ValidationError(f"Room {room_data['id']} does not exist.")
            if not room.can_fit(room_data['num_adults'], room_data['num_children']):
                raise ValidationError(f"Room {room_data['id']} does not have enough capacity.")
            room_data['room'] = room

        capacity_sum = sum(room["room"].capacity for room in rooms)
        if capacity_sum < total_people:
            raise ValidationError(
                "Selected rooms do not have enough capacity."
            )

        # 2️⃣ kolize rezervací
        for room in rooms:
            overlapping = room["room"].reservations.filter(
                status__in=[
                    ReservationStatus.NEW,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.PAYMENT_PENDING,
                    ReservationStatus.PAYED,
                ],
                check_in_date__lt=self.check_out_date,
                check_out_date__gt=self.check_in_date,
            ).exclude(id=self.id).exists()

            if overlapping:
                raise ValidationError(
                    f"Room {room['id']} is not available for selected dates."
                )


    @property
    def nights(self):
        if not self.check_in_date or not self.check_out_date:
            return 0
        return (self.check_out_date - self.check_in_date).days


    def calculate_price(self, rooms):
        """
            rooms: [
                {
                    "id",
                    "num_adults",
                    "num_children",
                }
            ]

            """
        price = 0

        for room_data in rooms:
            try:
                room = Room.objects.get(id=room_data['id'])
            except Room.DoesNotExist:
                raise ValidationError(f"Room {room_data['id']} does not exist.")

            price += room.calculate_price_per_day(room_data['num_adults'], room_data['num_children'])

        if self.nights == 0:
            return 0

        price = price * self.nights

        return price

