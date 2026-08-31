import pytest

from pension.guest.models import Guest
from pension.voucher.enums import VoucherStatus
from pension.voucher.models import VoucherOrder

pytestmark = pytest.mark.usefixtures("mock_emails")


def create_voucher_order(*, guest, status, delivery_method=VoucherOrder.DeliveryMethod.EMAIL):
    return VoucherOrder.objects.create(
        guest=guest,
        amount=1000,
        currency="CZK",
        delivery_method=delivery_method,
        status=status,
    )


@pytest.mark.django_db
def test_filter_by_status(staff_client):
    guest = Guest.objects.create(email="filter1@example.com", first_name="Filter", last_name="One")
    new_order = create_voucher_order(guest=guest, status=VoucherStatus.NEW)
    create_voucher_order(guest=guest, status=VoucherStatus.SENT)

    response = staff_client.get("/pension/admin/vouchers/", {"status": VoucherStatus.NEW})

    assert response.status_code == 200
    numbers = [item["number"] for item in response.data["results"]] if "results" in response.data else [
        item["number"] for item in response.data
    ]
    assert new_order.number in numbers


@pytest.mark.django_db
def test_filter_by_delivery_method(staff_client):
    guest = Guest.objects.create(email="filter2@example.com", first_name="Filter", last_name="Two")
    print_order = create_voucher_order(
        guest=guest, status=VoucherStatus.NEW, delivery_method=VoucherOrder.DeliveryMethod.PRINT
    )
    create_voucher_order(guest=guest, status=VoucherStatus.NEW, delivery_method=VoucherOrder.DeliveryMethod.EMAIL)

    response = staff_client.get("/pension/admin/vouchers/", {"delivery_method": "print"})

    assert response.status_code == 200
    numbers = [item["number"] for item in response.data["results"]] if "results" in response.data else [
        item["number"] for item in response.data
    ]
    assert print_order.number in numbers


@pytest.mark.django_db
def test_search_text_matches_guest_last_name(staff_client):
    guest = Guest.objects.create(email="search@example.com", first_name="Searchable", last_name="Uniquename")
    voucher_order = create_voucher_order(guest=guest, status=VoucherStatus.NEW)

    response = staff_client.get("/pension/admin/vouchers/", {"search_text": "Uniquename"})

    assert response.status_code == 200
    numbers = [item["number"] for item in response.data["results"]] if "results" in response.data else [
        item["number"] for item in response.data
    ]
    assert voucher_order.number in numbers