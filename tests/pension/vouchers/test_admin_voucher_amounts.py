from datetime import timedelta

import pytest
from django.utils import timezone

from pension.voucher.models import VoucherAmount
from pension.voucher.jobs import purge_deleted_voucher_amounts


@pytest.mark.django_db
def test_admin_can_create_update_and_soft_delete_voucher_amount(staff_client):
    create_response = staff_client.post(
        '/pension/admin/voucher-amounts/',
        {'value': '2500.00', 'currency': 'CZK', 'is_active': True, 'sort_order': 4},
        format='json',
    )

    assert create_response.status_code == 201
    amount_id = create_response.data['id']

    update_response = staff_client.put(
        f'/pension/admin/voucher-amounts/{amount_id}/',
        {'value': '3000.00', 'currency': 'CZK', 'is_active': True, 'sort_order': 5},
        format='json',
    )

    assert update_response.status_code == 200
    assert update_response.data['value'] == '3000.00'

    delete_response = staff_client.delete(f'/pension/admin/voucher-amounts/{amount_id}/')

    assert delete_response.status_code == 204
    amount = VoucherAmount.objects.get(id=amount_id)
    assert amount.deleted_at is not None
    assert amount.is_active

    voucher_response = staff_client.post(
        '/pension/public/vouchers/create/',
        {
            'guest': {
                'first_name': 'Jan',
                'last_name': 'Novak',
                'email': 'jan.novak@example.com',
            },
            'amount_id': amount_id,
            'delivery_method': 'email',
        },
        format='json',
    )

    assert voucher_response.status_code == 200


@pytest.mark.django_db
def test_public_voucher_amounts_excludes_soft_deleted_amount(auth_client, voucher_amount):
    voucher_amount.deleted_at = timezone.now()
    voucher_amount.save(update_fields=['deleted_at'])

    response = auth_client.get('/pension/public/vouchers/amounts/')

    assert response.status_code == 200
    assert voucher_amount.id not in {amount['id'] for amount in response.data}


@pytest.mark.django_db
def test_purge_deleted_voucher_amounts_removes_records_deleted_more_than_seven_days_ago():
    old_amount = VoucherAmount.objects.create(
        value=1000,
        deleted_at=timezone.now() - timedelta(days=8),
    )
    recent_amount = VoucherAmount.objects.create(
        value=1500,
        deleted_at=timezone.now() - timedelta(days=6),
    )

    purge_deleted_voucher_amounts()

    assert not VoucherAmount.objects.filter(id=old_amount.id).exists()
    assert VoucherAmount.objects.filter(id=recent_amount.id).exists()
