import pytest

from pension.voucher.enums import VoucherStatus
from pension.voucher.models import VoucherOrder

pytestmark = pytest.mark.usefixtures("mock_emails")


def voucher_payload(voucher_amount, **overrides):
    payload = {
        "guest": {
            "first_name": "Jana",
            "last_name": "Novakova",
            "email": "jana.novakova@example.com",
        },
        "amount_id": voucher_amount.id,
        "delivery_method": "email",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_create_voucher_order_email_delivery(auth_client, voucher_amount, mock_emails):
    payload = voucher_payload(voucher_amount)

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 200
    assert response.data["status"] == VoucherStatus.NEW
    assert float(response.data["amount"]) == 1000.0
    # guest confirmation + admin notification
    assert mock_emails.call_count == 2
    email_types = {call.kwargs["email_type"] for call in mock_emails.call_args_list}
    assert email_types == {"voucher_order_received", "admin_new_voucher_order"}


@pytest.mark.django_db
def test_create_voucher_order_notifies_admin(auth_client, voucher_amount, mock_emails, settings):
    payload = voucher_payload(voucher_amount)

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 200
    admin_calls = [
        call for call in mock_emails.call_args_list
        if call.kwargs["email_type"] == "admin_new_voucher_order"
    ]
    assert len(admin_calls) == 1
    assert admin_calls[0].kwargs["recipient"] == settings.ADMIN_NOTIFICATION_EMAIL


@pytest.mark.django_db
def test_create_voucher_order_skips_admin_notification_when_unconfigured(
    auth_client, voucher_amount, mock_emails, settings
):
    settings.ADMIN_NOTIFICATION_EMAIL = ""
    payload = voucher_payload(voucher_amount)

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 200
    assert mock_emails.call_count == 1
    assert mock_emails.call_args.kwargs["email_type"] == "voucher_order_received"


@pytest.mark.django_db
def test_create_voucher_order_print_requires_address(auth_client, voucher_amount):
    payload = voucher_payload(
        voucher_amount,
        delivery_method="print",
        guest={
            "first_name": "Petr",
            "last_name": "Svoboda",
            "email": "petr.svoboda@example.com",
        },
    )

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 400
    assert "shipping_street" in response.data


@pytest.mark.django_db
def test_create_voucher_order_print_with_full_address(auth_client, voucher_amount):
    payload = voucher_payload(
        voucher_amount,
        delivery_method="print",
        guest={
            "first_name": "Petr",
            "last_name": "Svoboda",
            "email": "petr.print@example.com",
        },
        shipping_street="Hlavni",
        shipping_house_number="12",
        shipping_city="Praha",
        shipping_postal_code="11000",
        shipping_country="Ceska republika",
    )

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 200
    assert response.data["delivery_method"] == "print"
    assert response.data["shipping_city"] == "Praha"


@pytest.mark.django_db
def test_create_voucher_order_requires_email(auth_client, voucher_amount):
    payload = voucher_payload(
        voucher_amount,
        guest={"first_name": "Bez", "last_name": "Emailu"},
    )

    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_voucher_status_list(auth_client):
    response = auth_client.get("/pension/public/vouchers/statuses/")
    assert response.status_code == 200
    assert len(response.data) == 4


@pytest.mark.django_db
def test_guest_reuse_by_email(auth_client, voucher_amount):
    payload1 = voucher_payload(voucher_amount)
    resp1 = auth_client.post("/pension/public/vouchers/create/", payload1, format="json")
    assert resp1.status_code == 200
    guest_id_1 = resp1.data["guest"]["id"]

    payload2 = voucher_payload(voucher_amount)
    resp2 = auth_client.post("/pension/public/vouchers/create/", payload2, format="json")
    assert resp2.status_code == 200
    guest_id_2 = resp2.data["guest"]["id"]

    assert guest_id_1 == guest_id_2


@pytest.mark.django_db
def test_voucher_number_is_generated(auth_client, voucher_amount):
    payload = voucher_payload(voucher_amount)
    response = auth_client.post("/pension/public/vouchers/create/", payload, format="json")

    voucher_order = VoucherOrder.objects.get(number=response.data["number"])
    assert voucher_order.number.startswith("V-")