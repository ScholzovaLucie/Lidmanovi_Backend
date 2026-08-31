import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.db import connection
from django.utils import timezone

from pension.voucher.models import VoucherAmount

LOGGER = logging.getLogger(__name__)
SCHEDULER = BackgroundScheduler(timezone=settings.TIME_ZONE)
LOCK_ID = 741852963


def purge_deleted_voucher_amounts():
    cutoff = timezone.now() - timedelta(days=7)

    if connection.vendor != 'postgresql':
        return VoucherAmount.objects.filter(deleted_at__lte=cutoff).delete()[0]

    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_try_advisory_lock(%s)', [LOCK_ID])
        acquired = cursor.fetchone()[0]

    if not acquired:
        return 0

    try:
        return VoucherAmount.objects.filter(deleted_at__lte=cutoff).delete()[0]
    finally:
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_unlock(%s)', [LOCK_ID])


def run_voucher_amount_cleanup():
    deleted_count = purge_deleted_voucher_amounts()
    if deleted_count:
        LOGGER.info('Permanently deleted %s voucher amount(s).', deleted_count)


def start_voucher_amount_cleanup_scheduler():
    if SCHEDULER.running:
        return

    SCHEDULER.add_job(
        run_voucher_amount_cleanup,
        trigger='interval',
        days=7,
        id='purge_deleted_voucher_amounts',
        replace_existing=True,
        next_run_time=timezone.now(),
    )
    SCHEDULER.start()
