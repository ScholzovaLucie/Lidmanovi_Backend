import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from pension.guest.models import Guest
from pension.voucher.enums import VoucherStatus
from pension.voucher.models import VoucherOrder


def create_voucher_order(*, guest, status=VoucherStatus.NEW, delivery_method=VoucherOrder.DeliveryMethod.EMAIL):
    return VoucherOrder.objects.create(
        guest=guest,
        amount=1000,
        currency="CZK",
        delivery_method=delivery_method,
        status=status,
    )


@pytest.mark.django_db
def test_admin_update_changes_status_and_sends_email(staff_client, mock_emails):
    guest = Guest.objects.create(email="update@example.com", first_name="Status", last_name="Update")
    voucher_order = create_voucher_order(guest=guest)

    response = staff_client.put(
        f"/pension/admin/vouchers/{voucher_order.id}/update/",
        {"status": VoucherStatus.CONFIRMED},
        format="json",
    )

    assert response.status_code == 200
    voucher_order.refresh_from_db()
    assert voucher_order.status == VoucherStatus.CONFIRMED
    mock_emails.assert_called_once()
    assert mock_emails.call_args.kwargs["email_type"] == "voucher_order_confirmed"


@pytest.mark.django_db
def test_admin_update_to_sent_sets_sent_at(staff_client, mock_emails):
    guest = Guest.objects.create(email="sent@example.com", first_name="Sent", last_name="Test")
    voucher_order = create_voucher_order(guest=guest, status=VoucherStatus.CONFIRMED)
    assert voucher_order.sent_at is None

    response = staff_client.put(
        f"/pension/admin/vouchers/{voucher_order.id}/update/",
        {"status": VoucherStatus.SENT},
        format="json",
    )

    assert response.status_code == 200
    voucher_order.refresh_from_db()
    assert voucher_order.status == VoucherStatus.SENT
    assert voucher_order.sent_at is not None
    assert mock_emails.call_args.kwargs["email_type"] == "voucher_order_sent"


@pytest.mark.django_db
def test_admin_update_to_cancelled_sends_email(staff_client, mock_emails):
    guest = Guest.objects.create(email="cancel@example.com", first_name="Cancel", last_name="Test")
    voucher_order = create_voucher_order(guest=guest)

    response = staff_client.put(
        f"/pension/admin/vouchers/{voucher_order.id}/update/",
        {"status": VoucherStatus.CANCELLED},
        format="json",
    )

    assert response.status_code == 200
    voucher_order.refresh_from_db()
    assert voucher_order.status == VoucherStatus.CANCELLED
    assert mock_emails.call_args.kwargs["email_type"] == "voucher_order_cancelled"


@pytest.mark.django_db
def test_status_update_forbidden_for_non_staff():
    guest = Guest.objects.create(email="forbidden@example.com", first_name="No", last_name="Access")
    voucher_order = create_voucher_order(guest=guest)

    non_staff_user = User.objects.create_user(username="user", password="user123")
    client = APIClient()
    client.force_authenticate(user=non_staff_user)

    response = client.put(
        f"/pension/admin/vouchers/{voucher_order.id}/update/",
        {"status": VoucherStatus.CONFIRMED},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_list_and_retrieve_vouchers(staff_client):
    guest = Guest.objects.create(email="list@example.com", first_name="List", last_name="Test")
    voucher_order = create_voucher_order(guest=guest)

    list_response = staff_client.get("/pension/admin/vouchers/")
    assert list_response.status_code == 200

    detail_response = staff_client.get(f"/pension/admin/vouchers/{voucher_order.id}/")
    assert detail_response.status_code == 200
    assert detail_response.data["number"] == voucher_order.number


@pytest.mark.django_db
def test_public_cannot_list_admin_vouchers():
    guest = Guest.objects.create(email="public@example.com", first_name="Public", last_name="Test")
    create_voucher_order(guest=guest)

    client = APIClient()
    response = client.get("/pension/admin/vouchers/")
    assert response.status_code in (401, 403)