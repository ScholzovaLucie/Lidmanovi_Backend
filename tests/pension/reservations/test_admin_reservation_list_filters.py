import pytest

from pension.guest.models import Guest
from pension.reservation.enums import ReservationStatus
from pension.reservation.models import Reservation
from pension.room.models import Room


def _create_reservation(*, guest, room, check_in, check_out, status):
    reservation = Reservation.objects.create(
        check_in_date=check_in,
        check_out_date=check_out,
        num_adults=1,
        num_children=0,
        status=status,
        primary_guest=guest,
        currency="CZK",
    )
    reservation.rooms.add(room)
    return reservation


@pytest.mark.django_db
def test_admin_list_filters_by_reservation_date_range(auth_client):
    guest = Guest.objects.create(first_name="Jan", last_name="Novak", email="range@example.com")
    room = Room.objects.create(
        name="Room A",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1000,
        price_for_children=0,
    )

    _create_reservation(
        guest=guest,
        room=room,
        check_in="2026-04-10",
        check_out="2026-04-12",
        status=ReservationStatus.NEW,
    )
    excluded = _create_reservation(
        guest=guest,
        room=room,
        check_in="2026-05-01",
        check_out="2026-05-03",
        status=ReservationStatus.NEW,
    )

    response = auth_client.get(
        "/pension/admin/reservations/",
        {
            "reservation_from": "2026-04-01",
            "reservation_to": "2026-04-30",
        },
    )

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data}
    assert excluded.id not in returned_ids
    assert len(returned_ids) == 1


@pytest.mark.django_db
def test_admin_list_filters_by_status_and_room(auth_client):
    guest = Guest.objects.create(first_name="Eva", last_name="Sova", email="status-room@example.com")
    room_1 = Room.objects.create(
        name="Room C",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1200,
        price_for_children=0,
    )
    room_2 = Room.objects.create(
        name="Room D",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1300,
        price_for_children=0,
    )

    included = _create_reservation(
        guest=guest,
        room=room_1,
        check_in="2026-07-01",
        check_out="2026-07-03",
        status=ReservationStatus.CONFIRMED,
    )
    _create_reservation(
        guest=guest,
        room=room_1,
        check_in="2026-07-05",
        check_out="2026-07-06",
        status=ReservationStatus.NEW,
    )
    _create_reservation(
        guest=guest,
        room=room_2,
        check_in="2026-07-07",
        check_out="2026-07-09",
        status=ReservationStatus.CONFIRMED,
    )

    response = auth_client.get(
        "/pension/admin/reservations/",
        {
            "status": ReservationStatus.CONFIRMED,
            "room_id": room_1.id,
        },
    )

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data}
    assert returned_ids == {included.id}
