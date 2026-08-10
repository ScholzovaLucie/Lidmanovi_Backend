from io import BytesIO

import openpyxl
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from pension.reservation.enums import ReservationStatus
from pension.reservation.models import Reservation
from pension.room.models import Room

BULK_IMPORT_URL = "/pension/admin/reservations/bulk-import/"

HEADERS = [
    "booking_reference",
    "check_in_date",
    "check_out_date",
    "room_name",
    "room_num_adults",
    "room_num_children",
    "guest_first_name",
    "guest_last_name",
    "guest_email",
    "guest_phone",
    "guest_country",
    "guest_note",
    "status",
    "currency",
    "note",
    "number",
    "price",
]


def build_upload(rows, headers=HEADERS, filename="import.xlsx"):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header, "") for header in headers])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        filename,
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def row(**overrides):
    base = {
        "booking_reference": "BK001",
        "check_in_date": "2027-01-10",
        "check_out_date": "2027-01-12",
        "room_num_adults": 2,
        "guest_first_name": "Jana",
        "guest_last_name": "Novakova",
        "guest_email": "jana@example.com",
    }
    base.update(overrides)
    return base


@pytest.mark.django_db
def test_bulk_import_creates_single_room_reservation(staff_client, room):
    upload = build_upload([row(room_name=room.name)])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    assert response.data["created"] == [{"booking_reference": "BK001", "number": response.data["created"][0]["number"], "room_count": 1}]
    assert response.data["skipped"] == []
    assert Reservation.objects.count() == 1

    reservation = Reservation.objects.get()
    assert reservation.primary_guest.first_name == "Jana"
    assert reservation.primary_guest.email == "jana@example.com"
    assert reservation.num_adults == 2
    assert reservation.num_children == 0
    assert reservation.status == ReservationStatus.NEW
    assert list(reservation.rooms.all()) == [room]


@pytest.mark.django_db
def test_bulk_import_groups_multi_room_booking_by_reference(staff_client):
    room_a = Room.objects.create(
        name="Room A", capacity=2, max_adults=2, max_children=0, price_for_adult=1000, price_for_children=0,
    )
    room_b = Room.objects.create(
        name="Room B", capacity=2, max_adults=2, max_children=0, price_for_adult=800, price_for_children=0,
    )
    upload = build_upload([
        row(room_name=room_a.name, room_num_adults=2),
        row(room_name=room_b.name, room_num_adults=1),
    ])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    assert len(response.data["created"]) == 1
    assert response.data["created"][0]["room_count"] == 2
    assert Reservation.objects.count() == 1

    reservation = Reservation.objects.get()
    assert reservation.num_adults == 3
    assert set(reservation.rooms.values_list("id", flat=True)) == {room_a.id, room_b.id}


@pytest.mark.django_db
def test_bulk_import_dry_run_does_not_persist(staff_client, room):
    upload = build_upload([row(room_name=room.name)])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload, "dry_run": "true"}, format="multipart")

    assert response.status_code == 200
    assert response.data["dry_run"] is True
    assert len(response.data["created"]) == 1
    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_bulk_import_skips_unknown_room(staff_client):
    upload = build_upload([row(room_name="Does not exist")])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    assert response.data["created"] == []
    assert len(response.data["skipped"]) == 1
    assert "does not exist" in response.data["skipped"][0]["errors"][0]
    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_bulk_import_skips_overlapping_dates(staff_client, room, guest):
    existing = Reservation.objects.create(
        check_in_date="2027-01-10",
        check_out_date="2027-01-12",
        num_adults=1,
        primary_guest=guest,
        status=ReservationStatus.CONFIRMED,
    )
    existing.rooms.add(room)

    upload = build_upload([row(room_name=room.name, room_num_adults=1)])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    assert response.data["created"] == []
    assert len(response.data["skipped"]) == 1
    assert "not available" in response.data["skipped"][0]["errors"][0]
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_bulk_import_applies_explicit_status_number_and_price(staff_client, room):
    upload = build_upload([row(
        room_name=room.name,
        status="confirmed",
        number="R-CUSTOM-1",
        price="12345",
    )])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    reservation = Reservation.objects.get()
    assert reservation.status == ReservationStatus.CONFIRMED
    assert reservation.number == "R-CUSTOM-1"
    assert float(reservation.price) == 12345.0


@pytest.mark.django_db
def test_bulk_import_rejects_duplicate_number_in_db(staff_client, room, guest):
    Reservation.objects.create(
        check_in_date="2020-01-01",
        check_out_date="2020-01-02",
        num_adults=1,
        primary_guest=guest,
        number="R-DUP-1",
    )
    upload = build_upload([row(room_name=room.name, number="R-DUP-1")])

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 200
    assert response.data["created"] == []
    assert "already exists" in response.data["skipped"][0]["errors"][0]


@pytest.mark.django_db
def test_bulk_import_rejects_missing_required_column(staff_client):
    headers = [h for h in HEADERS if h != "room_name"]
    upload = build_upload([row()], headers=headers)

    response = staff_client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 400
    assert "room_name" in str(response.data)


@pytest.mark.django_db
def test_bulk_import_forbidden_for_non_staff(room):
    non_staff_user = User.objects.create_user(username="guest-user", password="pass1234")
    client = APIClient()
    client.force_authenticate(user=non_staff_user)

    upload = build_upload([row(room_name=room.name)])
    response = client.post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 403


@pytest.mark.django_db
def test_bulk_import_unauthenticated_rejected(room):
    upload = build_upload([row(room_name=room.name)])
    response = APIClient().post(BULK_IMPORT_URL, {"file": upload}, format="multipart")

    assert response.status_code == 401
