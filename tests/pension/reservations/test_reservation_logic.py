from datetime import date

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from pension.guest.models import Guest
from pension.reservation.models import Reservation
from pension.reservation.serializers import ReservationCreateSerializer
from pension.room.models import Room

pytestmark = pytest.mark.usefixtures("mock_emails")


def _build_payload(check_in, check_out, email, room_id, num_adults=None, num_children=None):
    payload = {
        "check_in_date": check_in,
        "check_out_date": check_out,
        "currency": "CZK",
        "primary_guest": {
            "first_name": "Jan",
            "last_name": "Novak",
            "email": email,
        },
        "rooms": [
            {
                "id": room_id,
                "num_adults": 2,
                "num_children": 1,
            }
        ],
    }
    if num_adults is not None:
        payload["num_adults"] = num_adults
    if num_children is not None:
        payload["num_children"] = num_children
    return payload


@pytest.mark.django_db
def test_serializer_rejects_invalid_date_range():
    room = Room.objects.create(
        name="Pokoj logic-1",
        capacity=3,
        max_adults=2,
        max_children=1,
        price_for_adult=1000,
        price_for_children=500,
    )
    serializer = ReservationCreateSerializer(
        data=_build_payload("2026-04-10", "2026-04-10", "logic1@example.com", room.id)
    )

    assert serializer.is_valid() is False
    assert "check_out_date must be greater than check_in_date" in str(serializer.errors)


@pytest.mark.django_db
def test_serializer_reuses_same_guest_for_multiple_reservations():
    room = Room.objects.create(
        name="Pokoj logic-2",
        capacity=3,
        max_adults=2,
        max_children=1,
        price_for_adult=1000,
        price_for_children=500,
    )

    serializer_1 = ReservationCreateSerializer(
        data=_build_payload("2026-04-10", "2026-04-12", "reuse-logic@example.com", room.id)
    )
    assert serializer_1.is_valid(), serializer_1.errors
    reservation_1 = serializer_1.save()

    serializer_2 = ReservationCreateSerializer(
        data=_build_payload("2026-04-15", "2026-04-17", "reuse-logic@example.com", room.id)
    )
    assert serializer_2.is_valid(), serializer_2.errors
    reservation_2 = serializer_2.save()

    assert Guest.objects.filter(email="reuse-logic@example.com").count() == 1
    assert reservation_1.primary_guest_id == reservation_2.primary_guest_id
    assert reservation_1.number
    assert reservation_2.number
    assert reservation_1.number != reservation_2.number


@pytest.mark.django_db
def test_serializer_autofills_total_people_from_rooms_when_missing():
    room = Room.objects.create(
        name="Pokoj logic-3",
        capacity=3,
        max_adults=2,
        max_children=1,
        price_for_adult=1000,
        price_for_children=500,
    )

    serializer = ReservationCreateSerializer(
        data=_build_payload("2026-05-01", "2026-05-03", "autofill@example.com", room.id)
    )
    assert serializer.is_valid(), serializer.errors
    reservation = serializer.save()

    assert reservation.num_adults == 2
    assert reservation.num_children == 1


@pytest.mark.django_db
def test_validate_rooms_rejects_overlapping_reservation():
    room = Room.objects.create(
        name="Pokoj logic-4",
        capacity=3,
        max_adults=2,
        max_children=1,
        price_for_adult=1000,
        price_for_children=500,
    )
    guest = Guest.objects.create(first_name="A", last_name="B", email="overlap@example.com")

    existing = Reservation.objects.create(
        check_in_date=date(2026, 6, 10),
        check_out_date=date(2026, 6, 12),
        num_adults=2,
        num_children=0,
        primary_guest=guest,
    )
    existing.rooms.add(room)

    new_reservation = Reservation.objects.create(
        check_in_date=date(2026, 6, 11),
        check_out_date=date(2026, 6, 13),
        num_adults=2,
        num_children=0,
        primary_guest=guest,
    )

    with pytest.raises(DjangoValidationError, match="is not available for selected dates"):
        new_reservation.validate_rooms(
            [{"id": room.id, "num_adults": 2, "num_children": 0}]
        )


@pytest.mark.django_db
def test_calculate_price_uses_room_rates_and_nights():
    room = Room.objects.create(
        name="Pokoj logic-5",
        capacity=4,
        max_adults=3,
        max_children=2,
        price_for_adult=1000,
        price_for_children=500,
    )
    guest = Guest.objects.create(first_name="Cena", last_name="Test", email="price@example.com")
    reservation = Reservation.objects.create(
        check_in_date=date(2026, 7, 1),
        check_out_date=date(2026, 7, 4),
        num_adults=2,
        num_children=1,
        primary_guest=guest,
    )

    price = reservation.calculate_price(
        [{"id": room.id, "num_adults": 2, "num_children": 1}]
    )

    # (2 * 1000 + 1 * 500) * 3 nights
    assert price == 7500
