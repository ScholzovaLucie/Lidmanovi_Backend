import pytest

from pension.guest.models import Guest
from pension.reservation.models import Reservation
from pension.room.models import Room

pytestmark = pytest.mark.usefixtures("mock_emails")


def _reservation_payload(check_in_date, check_out_date, guest_email, room_id):
    return {
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "currency": "CZK",
        "primary_guest": {
            "first_name": "Jan",
            "last_name": "Novak",
            "email": guest_email,
        },
        "rooms": [
            {
                "id": room_id,
                "num_adults": 2,
                "num_children": 0,
            }
        ],
    }


@pytest.mark.django_db
def test_can_create_multiple_operations_for_one_client(auth_client, mock_emails):
    room = Room.objects.create(
        name="Pokoj 101",
        capacity=3,
        price_for_adult=1000,
        price_for_children=500,
    )

    payload_1 = _reservation_payload("2026-03-10", "2026-03-12", "klient@example.com", room.id)
    payload_2 = _reservation_payload("2026-03-15", "2026-03-17", "klient@example.com", room.id)

    resp_1 = auth_client.post("/pension/public/reservations/create/", payload_1, format="json")
    resp_2 = auth_client.post("/pension/public/reservations/create/", payload_2, format="json")

    assert resp_1.status_code == 200
    assert resp_2.status_code == 200
    assert Guest.objects.count() == 1

    guest = Guest.objects.get(email="klient@example.com")
    assert Reservation.objects.filter(primary_guest=guest).count() == 2
    assert mock_emails.call_count == 2
