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
    assert response.data["count"] == 1
    returned_ids = {item["id"] for item in response.data["results"]}
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
    assert response.data["count"] == 1
    returned_ids = {item["id"] for item in response.data["results"]}
    assert returned_ids == {included.id}


@pytest.mark.django_db
def test_admin_list_filters_by_primary_guest_email_and_last_name(auth_client):
    room = Room.objects.create(
        name="Room E",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1500,
        price_for_children=0,
    )
    guest_target = Guest.objects.create(first_name="Petr", last_name="Kral", email="kral@example.com")
    guest_other = Guest.objects.create(first_name="Milan", last_name="Simek", email="simek@example.com")

    by_email = _create_reservation(
        guest=guest_target,
        room=room,
        check_in="2026-08-01",
        check_out="2026-08-03",
        status=ReservationStatus.NEW,
    )
    by_last_name = _create_reservation(
        guest=guest_target,
        room=room,
        check_in="2026-08-05",
        check_out="2026-08-06",
        status=ReservationStatus.CONFIRMED,
    )
    _create_reservation(
        guest=guest_other,
        room=room,
        check_in="2026-08-07",
        check_out="2026-08-09",
        status=ReservationStatus.NEW,
    )

    response_email = auth_client.get(
        "/pension/admin/reservations/",
        {"primary_guest_email": "KRAL@example.com"},
    )
    assert response_email.status_code == 200
    assert response_email.data["count"] == 2
    returned_ids_email = {item["id"] for item in response_email.data["results"]}
    assert by_email.id in returned_ids_email
    assert by_last_name.id in returned_ids_email

    response_last_name = auth_client.get(
        "/pension/admin/reservations/",
        {"primary_guest_last_name": "kr"},
    )
    assert response_last_name.status_code == 200
    assert response_last_name.data["count"] == 2
    returned_ids_last_name = {item["id"] for item in response_last_name.data["results"]}
    assert returned_ids_last_name == {by_email.id, by_last_name.id}


@pytest.mark.django_db
def test_admin_list_filters_by_primary_guest_id(auth_client):
    room = Room.objects.create(
        name="Room F",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1100,
        price_for_children=0,
    )
    guest_target = Guest.objects.create(first_name="Klient", last_name="Cil", email="cil@example.com")
    guest_other = Guest.objects.create(first_name="Jiny", last_name="Klient", email="jiny@example.com")

    expected = _create_reservation(
        guest=guest_target,
        room=room,
        check_in="2026-09-01",
        check_out="2026-09-03",
        status=ReservationStatus.NEW,
    )
    _create_reservation(
        guest=guest_other,
        room=room,
        check_in="2026-09-05",
        check_out="2026-09-06",
        status=ReservationStatus.NEW,
    )

    response = auth_client.get(
        "/pension/admin/reservations/",
        {"primary_guest_id": guest_target.id},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    returned_ids = {item["id"] for item in response.data["results"]}
    assert returned_ids == {expected.id}


@pytest.mark.django_db
def test_admin_list_filters_by_search_text_across_string_fields(auth_client):
    room = Room.objects.create(
        name="Panorama Deluxe",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1700,
        price_for_children=0,
        description="Pokoj s vyhledem",
    )
    guest_target = Guest.objects.create(
        first_name="Lucie",
        last_name="Scholzova",
        email="lucie@example.com",
        phone="+420777123456",
    )
    guest_other = Guest.objects.create(
        first_name="Pavel",
        last_name="Novotny",
        email="pavel@example.com",
        phone="+420777000000",
    )

    expected = _create_reservation(
        guest=guest_target,
        room=room,
        check_in="2026-10-01",
        check_out="2026-10-04",
        status=ReservationStatus.NEW,
    )
    expected.note = "Prijede pozde vecer"
    expected.save(update_fields=["note"])

    _create_reservation(
        guest=guest_other,
        room=room,
        check_in="2026-10-05",
        check_out="2026-10-06",
        status=ReservationStatus.NEW,
    )

    response_email = auth_client.get("/pension/admin/reservations/", {"search_text": "LUCIE@example.com"})
    assert response_email.status_code == 200
    assert response_email.data["count"] == 1
    assert {item["id"] for item in response_email.data["results"]} == {expected.id}

    response_name = auth_client.get("/pension/admin/reservations/", {"search_text": "scholz"})
    assert response_name.status_code == 200
    assert response_name.data["count"] == 1
    assert {item["id"] for item in response_name.data["results"]} == {expected.id}

    response_phone = auth_client.get("/pension/admin/reservations/", {"search_text": "123456"})
    assert response_phone.status_code == 200
    assert response_phone.data["count"] == 1
    assert {item["id"] for item in response_phone.data["results"]} == {expected.id}

    response_number = auth_client.get("/pension/admin/reservations/", {"search_text": expected.number})
    assert response_number.status_code == 200
    assert response_number.data["count"] == 1
    assert {item["id"] for item in response_number.data["results"]} == {expected.id}


@pytest.mark.django_db
def test_admin_by_status_returns_paginated_results(auth_client):
    room = Room.objects.create(
        name="Room G",
        capacity=2,
        max_adults=2,
        max_children=0,
        price_for_adult=1400,
        price_for_children=0,
    )
    guest = Guest.objects.create(first_name="Alena", last_name="Nova", email="alena@example.com")

    first = _create_reservation(
        guest=guest,
        room=room,
        check_in="2026-11-01",
        check_out="2026-11-02",
        status=ReservationStatus.NEW,
    )
    second = _create_reservation(
        guest=guest,
        room=room,
        check_in="2026-11-03",
        check_out="2026-11-04",
        status=ReservationStatus.NEW,
    )

    response = auth_client.get(
        "/pension/admin/reservations/by-status/",
        {"status": ReservationStatus.NEW, "page_size": 1},
    )

    assert response.status_code == 200
    assert response.data["count"] >= 2
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] in {first.id, second.id}
    assert response.data["next"] is not None
