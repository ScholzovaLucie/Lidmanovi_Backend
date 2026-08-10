import secrets
import string

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from pension.guest.models import Guest
from pension.reservation.enums import ReservationStatus
from pension.room.models import Room


STATUS_MAP_TO_MAIL = {
    ReservationStatus.NEW: "reservation_received",
    ReservationStatus.CONFIRMED: "reservation_approved",
    ReservationStatus.CANCELLED: "reservation_rejected",
    ReservationStatus.PAYED: "reservation_payd",
    ReservationStatus.DONE: "reservation_done",
}


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField(db_index=True)
    check_out_date = models.DateField(db_index=True)

    number = models.CharField(max_length=20, unique=True)

    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.NEW,
        db_index=True,
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
        blank=True,
        related_name="reservations"
    )

    _MAX_NUMBER_ATTEMPTS = 10

    @staticmethod
    def _generate_number():
        date_part = timezone.now().strftime("%Y%m%d")
        alphabet = string.digits
        for _ in range(Reservation._MAX_NUMBER_ATTEMPTS):
            suffix = ''.join(secrets.choice(alphabet) for _ in range(6))
            number = f"R-{date_part}-{suffix}"
            if not Reservation.objects.filter(number=number).exists():
                return number
        raise RuntimeError("Could not generate a unique reservation number after multiple attempts.")

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def validate_rooms(self, rooms, lock=False):
        """
        rooms: [{"id", "num_adults", "num_children"}]
        Enriches each room dict with a 'room' key containing the Room instance.

        lock: if True, locks the room rows (SELECT ... FOR UPDATE) for the duration of the
        enclosing transaction, so two concurrent bookings for the same room/dates can't both
        pass the overlap check before either commits. Must only be used inside
        transaction.atomic() - callers that just want a read-only preview (e.g. dry-run
        validation) should leave this False.
        """
        if not rooms:
            raise ValidationError("At least one room must be selected.")

        room_ids = [r['id'] for r in rooms]
        room_queryset = Room.objects.select_for_update() if lock else Room.objects.all()
        rooms_map = {r.id: r for r in room_queryset.filter(id__in=room_ids)}

        total_people = self.num_adults + self.num_children

        for room_data in rooms:
            room = rooms_map.get(room_data['id'])
            if room is None:
                raise ValidationError(f"Room {room_data['id']} does not exist.")
            if not room.can_fit(room_data['num_adults'], room_data['num_children']):
                raise ValidationError(f"Room {room_data['id']} does not have enough capacity.")
            room_data['room'] = room

        capacity_sum = sum(room_data['room'].capacity for room_data in rooms)
        if capacity_sum < total_people:
            raise ValidationError("Selected rooms do not have enough capacity.")

        for room_data in rooms:
            overlapping = room_data['room'].reservations.filter(
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
                    f"Room {room_data['id']} is not available for selected dates."
                )

    @property
    def nights(self):
        if not self.check_in_date or not self.check_out_date:
            return 0
        return (self.check_out_date - self.check_in_date).days

    def calculate_price(self, rooms):
        """
        rooms: [{"id", "num_adults", "num_children", "room"?}]
        Uses cached 'room' key if present (set by validate_rooms), otherwise fetches.
        """
        price = 0
        for room_data in rooms:
            room = room_data.get('room')
            if room is None:
                try:
                    room = Room.objects.get(id=room_data['id'])
                except Room.DoesNotExist:
                    raise ValidationError(f"Room {room_data['id']} does not exist.")
            price += room.calculate_price_per_day(room_data['num_adults'], room_data['num_children'])

        if self.nights == 0:
            return 0

        return price * self.nights
