import pytest

from pension.guest.models import Guest
from pension.reservation.enums import ReservationStatus
from pension.reservation.models import Reservation
from pension.room.models import Room


@pytest.mark.django_db
def test_admin_update_changes_status_and_persists(staff_client, mock_emails):
    room = Room.objects.create(
        name="Test room for update",
        capacity=4,
        price_for_adult=1000,
        price_for_children=500,
    )
    guest = Guest.objects.create(
        email="status-update@example.com",
        first_name="Status",
        last_name="Update",
    )
    reservation = Reservation.objects.create(
        check_in_date="2026-03-10",
        check_out_date="2026-03-12",
        num_adults=2,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )
    reservation.rooms.add(room)

    response = staff_client.put(
        f"/pension/admin/reservations/{reservation.id}/update/",
        {"status": ReservationStatus.CONFIRMED},
        format="json",
    )

    assert response.status_code == 200
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CONFIRMED
    assert response.data["status"] == ReservationStatus.CONFIRMED
    mock_emails.assert_called_once()
