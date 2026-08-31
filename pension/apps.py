import os
import sys

from django.apps import AppConfig


class PensionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pension'

    def ready(self):
        if 'pytest' in sys.modules:
            return

        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            from pension.voucher.jobs import start_voucher_amount_cleanup_scheduler

            start_voucher_amount_cleanup_scheduler()
