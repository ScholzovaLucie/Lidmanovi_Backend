import pytest
from django.contrib.auth.models import User
from pension.reservation.models import Reservation, Guest
from pension.room.models import Room
from pension.reservation.enums import ReservationStatus
from rest_framework.test import APIClient

pytestmark = pytest.mark.usefixtures("mock_emails")


def reservation_payload(room, guest, **overrides):
    payload = {
        "check_in_date": "2026-02-10",
        "check_out_date": "2026-02-12",
        "num_adults": 2,
        "num_children": 1,
        "rooms": [
            {
                "id": room.id,
                "num_adults": 2,
                "num_children": 1,
            }
        ],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
        },
    }
    payload.update(overrides)
    return payload


def create_existing_reservation(*, room, guest, check_in_date, check_out_date, status, num_adults=1, num_children=0):
    reservation = Reservation.objects.create(
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        num_adults=num_adults,
        num_children=num_children,
        primary_guest=guest,
        status=status,
        currency="CZK",
    )
    reservation.rooms.add(room)
    return reservation


@pytest.mark.django_db
def test_create_reservation(auth_client, room, guest):
    payload = reservation_payload(room, guest)

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert response.status_code == 200
    assert response.data["num_adults"] == 2

@pytest.mark.django_db
def test_reservation_collision(auth_client, room, guest):
    create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=2,
        num_children=0,
        status=ReservationStatus.NEW,
    )

    payload = reservation_payload(
        room,
        guest,
        check_in_date="2026-02-11",
        check_out_date="2026-02-13",
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 2, "num_children": 0}],
    )

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_status_list(auth_client):
    response = auth_client.get("/pension/public/reservations/statuses/")
    assert response.status_code == 200
    assert len(response.data) > 0


# --- Additional tests for comprehensive scenario coverage ---

@pytest.mark.django_db
def test_invalid_dates_equal(auth_client, room, guest):
    guest_data = Guest(first_name="John", last_name="Doe", email="a@a.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-10",
        check_out_date="2026-02-10",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_invalid_dates_checkout_before_checkin(auth_client, room, guest):
    guest_data = Guest(first_name="Jane", last_name="Doe", email="b@b.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-12",
        check_out_date="2026-02-10",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_guest_reuse_by_email_and_document(auth_client, room):
    guest_email = "reuse@example.com"
    guest_data = Guest(first_name="John", last_name="Doe", email=guest_email)
    payload1 = reservation_payload(
        room,
        guest_data,
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp1 = auth_client.post("/pension/public/reservations/create/", payload1, format="json")
    assert resp1.status_code == 200
    guest_id_1 = resp1.data["primary_guest"]["id"]

    payload2 = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-13",
        check_out_date="2026-02-15",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp2 = auth_client.post("/pension/public/reservations/create/", payload2, format="json")
    assert resp2.status_code == 200
    guest_id_2 = resp2.data["primary_guest"]["id"]
    assert guest_id_1 == guest_id_2

@pytest.mark.django_db
def test_existing_guest_not_duplicated_with_full_data(auth_client, room, guest):
    payload = reservation_payload(
        room,
        guest,
        check_in_date="2026-03-01",
        check_out_date="2026-03-03",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )

    payload_second = reservation_payload(
        room,
        guest,
        check_in_date="2026-03-04",
        check_out_date="2026-03-05",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )

    resp1 = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp1.status_code == 200
    guest_id_1 = resp1.data["primary_guest"]["id"]

    resp2 = auth_client.post("/pension/public/reservations/create/", payload_second, format="json")
    assert resp2.status_code == 200
    guest_id_2 = resp2.data["primary_guest"]["id"]

    assert guest_id_1 == guest_id_2


@pytest.mark.django_db
def test_duplicit_reservation_in_sa_day(auth_client, room, guest):
    payload = reservation_payload(
        room,
        guest,
        check_in_date="2026-03-01",
        check_out_date="2026-03-03",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )

    resp1 = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp1.status_code == 200

    resp2 = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp2.status_code == 400
    if isinstance(resp2.data, list):
        assert "not available" in resp2.data[0]
    else:
        assert "not available" in resp2.data["non_field_errors"][0]


@pytest.mark.django_db
def test_room_capacity_exceeded_with_only_adults(auth_client, room):
    guest_data = Guest(first_name="Test", last_name="User", email="overadults@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        num_adults=room.capacity + 1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": room.capacity + 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_room_capacity_exceeded_with_mostly_children(auth_client, room):
    guest_data = Guest(first_name="Test", last_name="User", email="overchildren@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        num_adults=1,
        num_children=room.capacity,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": room.capacity}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_room_capacity_too_many_total(auth_client, room):
    guest_data = Guest(first_name="Test", last_name="User", email="overtotal@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        num_adults=room.capacity,
        num_children=1,
        rooms=[{"id": room.id, "num_adults": room.capacity, "num_children": 1}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_overlap_touching_boundaries_allowed(auth_client, room, guest):
    create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        status=ReservationStatus.NEW,
    )
    guest_data = Guest(first_name="Test", last_name="User", email="touching@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-12",
        check_out_date="2026-02-14",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_overlap_same_day_not_allowed(auth_client, room, guest):
    create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        status=ReservationStatus.CONFIRMED,
    )
    guest_data = Guest(first_name="Test", last_name="User", email="overlap@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-11",
        check_out_date="2026-02-13",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 400

@pytest.mark.django_db
@pytest.mark.parametrize("status", [ReservationStatus.CANCELLED, ReservationStatus.DONE])
def test_cancelled_and_done_reservations_do_not_block(auth_client, room, guest, status):
    create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        status=status,
    )
    guest_data = Guest(first_name="Test", last_name="User", email="notblocked@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-02-11",
        check_out_date="2026-02-13",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )
    resp = auth_client.post("/pension/public/reservations/create/", payload, format="json")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_status_update_forbidden_for_non_staff(auth_client, room, guest):
    reservation = create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        status=ReservationStatus.NEW,
    )
    non_staff_user = User.objects.create_user(username="user", password="user123")
    client = APIClient()
    client.force_authenticate(user=non_staff_user)
    update_payload = {"status": ReservationStatus.CONFIRMED}
    resp = client.put(f"/pension/admin/reservations/{reservation.id}/update/", update_payload, format="json")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_status_update_allowed_for_staff(staff_client, staff_user, room, guest):
    reservation = create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=1,
        num_children=0,
        status=ReservationStatus.NEW,
    )
    update_payload = {"status": ReservationStatus.CONFIRMED}
    resp = staff_client.put(f"/pension/admin/reservations/{reservation.id}/update/", update_payload, format="json")
    assert resp.status_code in (200, 202)
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CONFIRMED


@pytest.mark.django_db
def test_note_in_operation_creation(auth_client, room, guest):
    payload = reservation_payload(room, guest, note="This is a note")

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    reservation_id = response.data["id"]

    assert response.status_code == 200
    assert Reservation.objects.filter(id=reservation_id).first().note == "This is a note"


@pytest.mark.django_db
def test_frontend_message_field_is_saved_as_reservation_note(auth_client, room, guest):
    payload = reservation_payload(room, guest)
    payload.pop("note", None)
    payload["message"] = "Frontend reservation message"

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    reservation_id = response.data["id"]

    assert response.status_code == 200
    assert Reservation.objects.filter(id=reservation_id).first().note == "Frontend reservation message"


@pytest.mark.django_db
@pytest.mark.parametrize("status", [ReservationStatus.PAYMENT_PENDING, ReservationStatus.PAYED])
def test_payment_pending_and_payed_reservations_do_block(auth_client, room, guest, status):
    create_existing_reservation(
        room=room,
        guest=guest,
        check_in_date="2026-03-10",
        check_out_date="2026-03-12",
        num_adults=1,
        num_children=0,
        status=status,
    )
    guest_data = Guest(first_name="Blocked", last_name="User", email=f"{status}@example.com")
    payload = reservation_payload(
        room,
        guest_data,
        check_in_date="2026-03-11",
        check_out_date="2026-03-13",
        num_adults=1,
        num_children=0,
        rooms=[{"id": room.id, "num_adults": 1, "num_children": 0}],
    )

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_reservation_rejects_unknown_room_id(auth_client, guest):
    payload = {
        "check_in_date": "2026-04-01",
        "check_out_date": "2026-04-03",
        "num_adults": 1,
        "num_children": 0,
        "rooms": [{"id": 999999, "num_adults": 1, "num_children": 0}],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
        },
    }

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_reservation_rejects_duplicate_room_ids(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-04-10",
        "check_out_date": "2026-04-12",
        "num_adults": 2,
        "num_children": 0,
        "rooms": [
            {"id": room.id, "num_adults": 1, "num_children": 0},
            {"id": room.id, "num_adults": 1, "num_children": 0},
        ],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
        },
    }

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 400
    assert "Each room can only be selected once." in str(response.data)


@pytest.mark.django_db
def test_create_reservation_rejects_inactive_room(auth_client, guest):
    inactive_room = Room.objects.create(
        name="Inactive room",
        capacity=2,
        price_for_adult=900,
        price_for_children=0,
        is_active=False,
    )
    payload = {
        "check_in_date": "2026-04-15",
        "check_out_date": "2026-04-17",
        "num_adults": 1,
        "num_children": 0,
        "rooms": [{"id": inactive_room.id, "num_adults": 1, "num_children": 0}],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
        },
    }

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 400
    assert "Room is not active" in str(response.data)


@pytest.mark.django_db
def test_create_reservation_rejects_mismatched_total_people_vs_rooms(auth_client, room, guest):
    payload = {
        "check_in_date": "2026-04-20",
        "check_out_date": "2026-04-22",
        "num_adults": 1,
        "num_children": 0,
        "rooms": [{"id": room.id, "num_adults": 2, "num_children": 0}],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": guest.email,
        },
    }

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 400
    assert "Total adults must match" in str(response.data)


@pytest.mark.django_db
def test_create_reservation_calculates_price_for_multiple_rooms(auth_client, guest):
    first_room = Room.objects.create(
        name="Multi room A",
        capacity=3,
        price_for_adult=1000,
        price_for_children=500,
    )
    second_room = Room.objects.create(
        name="Multi room B",
        capacity=2,
        price_for_adult=800,
        price_for_children=200,
    )

    payload = {
        "check_in_date": "2026-05-01",
        "check_out_date": "2026-05-04",
        "num_adults": 3,
        "num_children": 2,
        "currency": "CZK",
        "rooms": [
            {"id": first_room.id, "num_adults": 2, "num_children": 1},
            {"id": second_room.id, "num_adults": 1, "num_children": 1},
        ],
        "primary_guest": {
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "email": "multi-price@example.com",
        },
    }

    response = auth_client.post("/pension/public/reservations/create/", payload, format="json")

    assert response.status_code == 200
    assert float(response.data["price"]) == 10500.0
