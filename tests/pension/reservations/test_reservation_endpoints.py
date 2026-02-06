from pension.reservation.models import Reservation

import pytest
from pension.reservation.models import Reservation, Guest
from pension.room.models import Room
from pension.reservation.enums import ReservationStatus


@pytest.mark.django_db
def test_create_reservation(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": 2,
        "num_children": 1,
        "room": room.id,
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
            "document_number": guest.document_number
        },
        "items": []
    }

    response = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert response.status_code == 200
    assert response.data["num_adults"] == 2

@pytest.mark.django_db
def test_reservation_collision(auth_client, room, guest):
    Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=2,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )

    payload = {
        "check_in_date": "2026-02-11",
        "check_out_date": "2026-02-13",
        "num_adults": 2,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
            "document_number": guest.document_number
        },
        "items": []
    }

    response = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_status_list(auth_client):
    response = auth_client.get("/pension/reservations/statuses/")
    assert response.status_code == 200
    assert len(response.data) > 0


# --- Additional tests for comprehensive scenario coverage ---

@pytest.mark.django_db
def test_invalid_dates_equal(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-10",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "a@a.com",
            "document_number": "X123",
            "first_name": "John",
            "last_name": "Doe"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_invalid_dates_checkout_before_checkin(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-02-12",
        "check_out_date": "2026-02-10",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "b@b.com",
            "document_number": "Y456",
            "first_name": "Jane",
            "last_name": "Doe"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_guest_reuse_by_email_and_document(auth_client, room):
    guest_email = "reuse@example.com"
    guest_doc = "DOC123"
    payload1 = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": guest_email,
            "document_number": guest_doc,
            "first_name": "John",
            "last_name": "Doe"
        },
        "items": []
    }
    resp1 = auth_client.post("/pension/reservations/create/", payload1, format="json")
    assert resp1.status_code == 200
    guest_id_1 = resp1.data["primary_guest"]["id"]

    payload2 = {
        "check_in_date": "2026-02-13",
        "check_out_date": "2026-02-15",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": guest_email,
            "document_number": guest_doc,
            "first_name": "John",
            "last_name": "Doe"
        },
        "items": []
    }
    resp2 = auth_client.post("/pension/reservations/create/", payload2, format="json")
    assert resp2.status_code == 200
    guest_id_2 = resp2.data["primary_guest"]["id"]
    assert guest_id_1 == guest_id_2

@pytest.mark.django_db
def test_existing_guest_not_duplicated_with_full_data(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-03-01",
        "check_out_date": "2026-03-03",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
            "document_number": guest.document_number
        },
        "items": []
    }

    payload_second = {
        "check_in_date": "2026-03-04",
        "check_out_date": "2026-03-05",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
            "document_number": guest.document_number
        },
        "items": []
    }

    resp1 = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp1.status_code == 200
    guest_id_1 = resp1.data["primary_guest"]["id"]

    resp2 = auth_client.post("/pension/reservations/create/", payload_second, format="json")
    assert resp2.status_code == 200
    guest_id_2 = resp2.data["primary_guest"]["id"]

    assert guest_id_1 == guest_id_2


@pytest.mark.django_db
def test_duplicit_reservation_in_sa_day(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-03-01",
        "check_out_date": "2026-03-03",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
            "document_number": guest.document_number
        },
        "items": []
    }

    resp1 = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp1.status_code == 200

    resp2 = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp2.status_code == 400
    assert resp2.data["non_field_errors"][0] == "Room is not available for selected dates or capacity."


@pytest.mark.django_db
def test_room_capacity_too_many_adults(auth_client, room):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": room.max_adults + 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "overadults@example.com",
            "document_number": "CAPAD",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_room_capacity_too_many_children(auth_client, room):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": 1,
        "num_children": room.max_children + 1,
        "room": room.id,
        "primary_guest": {
            "email": "overchildren@example.com",
            "document_number": "CAPCH",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_room_capacity_too_many_total(auth_client, room):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": room.capacity,
        "num_children": 1,
        "room": room.id,
        "primary_guest": {
            "email": "overtotal@example.com",
            "document_number": "CAPTOT",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_overlap_touching_boundaries_allowed(auth_client, room, guest):
    # Existing reservation
    Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )
    # New reservation starts at existing check_out (should be allowed)
    payload = {
        "check_in_date": "2026-02-12",
        "check_out_date": "2026-02-14",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "touching@example.com",
            "document_number": "TOUCH",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_overlap_same_day_not_allowed(auth_client, room, guest):
    Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.CONFIRMED,
    )
    # New reservation overlaps on same day
    payload = {
        "check_in_date": "2026-02-11",
        "check_out_date": "2026-02-13",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "overlap@example.com",
            "document_number": "OVER",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
@pytest.mark.parametrize("status", [ReservationStatus.CANCELLED, ReservationStatus.DONE])
def test_cancelled_and_done_reservations_do_not_block(auth_client, room, guest, status):
    Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        primary_guest=guest,
        status=status,
    )
    payload = {
        "check_in_date": "2026-02-11",
        "check_out_date": "2026-02-13",
        "num_adults": 1,
        "num_children": 0,
        "room": room.id,
        "primary_guest": {
            "email": "notblocked@example.com",
            "document_number": "NOTBLK",
            "first_name": "Test",
            "last_name": "User"
        },
        "items": []
    }
    resp = auth_client.post("/pension/reservations/create/", payload, format="json")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_status_update_forbidden_for_non_staff(auth_client, room, guest):
    # Create a reservation
    reservation = Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )
    update_payload = {"status": ReservationStatus.CONFIRMED}
    resp = auth_client.put(f"/pension/reservations/{reservation.id}/update/", update_payload, format="json")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_status_update_allowed_for_staff(staff_client, staff_user, room, guest):
    reservation = Reservation.objects.create(
        room=room,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )
    update_payload = {"status": ReservationStatus.CONFIRMED}
    resp = staff_client.put(f"/pension/reservations/{reservation.id}/update/", update_payload, format="json")
    assert resp.status_code in (200, 202)
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CONFIRMED