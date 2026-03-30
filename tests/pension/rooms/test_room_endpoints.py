import pytest
from pension.room.models import Room
from pension.reservation.models import Reservation, Guest
from pension.reservation.enums import ReservationStatus

pytestmark = pytest.mark.usefixtures("mock_emails")

@pytest.mark.django_db
def test_room_availability_available_when_no_reservations(auth_client, room):
    # Room should be available if there are no reservations
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&to_date=2026-02-12&adults=2&children=0"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is True

@pytest.mark.django_db
def test_room_unavailable_when_overlapping_blocking_reservation(auth_client, room, guest):
    reservation = Reservation.objects.create(
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=2,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.CONFIRMED,
    )
    reservation.rooms.add(room)

    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-11&to_date=2026-02-13&adults=2&children=0"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is False

@pytest.mark.django_db
@pytest.mark.parametrize("status", [ReservationStatus.CANCELLED, ReservationStatus.DONE])
def test_room_available_when_overlap_with_cancelled_or_done(auth_client, room, guest, status):
    res = Reservation.objects.create(
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=2,
        num_children=0,
        primary_guest=guest,
        status=status,
    )
    res.rooms.add(room)
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-11&to_date=2026-02-13&adults=2&children=0"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is True

@pytest.mark.django_db
def test_room_available_when_dates_touch_at_boundary(auth_client, room, guest):
    res = Reservation.objects.create(
        check_in_date="2026-02-10",
        check_out_date="2026-02-12",
        num_adults=2,
        num_children=0,
        primary_guest=guest,
        status=ReservationStatus.NEW,
    )
    res.rooms.add(room)
    # New request starts at check_out (touches boundary, should be available)
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-12&to_date=2026-02-14&adults=2&children=0"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is True

@pytest.mark.django_db
def test_room_capacity_too_many_adults(auth_client, room):
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&to_date=2026-02-12&adults={room.max_adults+1}&children=0"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is False

@pytest.mark.django_db
def test_room_capacity_too_many_children(auth_client, room):
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&to_date=2026-02-12&adults=1&children={room.max_children+1}"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is False

@pytest.mark.django_db
def test_room_capacity_too_many_total(auth_client, room):
    total = room.capacity + 1
    # Try to split between adults and children
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&to_date=2026-02-12&adults={room.capacity}&children=1"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["available"] is False

@pytest.mark.django_db
def test_room_availability_missing_from_date_or_to_date(auth_client, room):
    url = f"/pension/public/rooms/{room.id}/availability/?to_date=2026-02-12&adults=1&children=0"
    response = auth_client.get(url)
    assert response.status_code == 400
    url2 = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&adults=1&children=0"
    response2 = auth_client.get(url2)
    assert response2.status_code == 400

@pytest.mark.django_db
def test_room_availability_invalid_date_range(auth_client, room):
    # from_date >= to_date should fail
    url = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-12&to_date=2026-02-10&adults=1&children=0"
    response = auth_client.get(url)
    assert response.status_code == 400
    url2 = f"/pension/public/rooms/{room.id}/availability/?from_date=2026-02-10&to_date=2026-02-10&adults=1&children=0"
    response2 = auth_client.get(url2)
    assert response2.status_code == 400
