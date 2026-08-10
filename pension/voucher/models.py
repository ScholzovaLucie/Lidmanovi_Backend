import secrets
import string

from django.db import models
from django.utils import timezone

from pension.guest.models import Guest


class VoucherAmount(models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="CZK")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "value"]

    def __str__(self):
        return f"{self.value} {self.currency}"


class VoucherOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    number = models.CharField(max_length=20, unique=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="CZK")

    note = models.TextField(blank=True)

    guest = models.ForeignKey(
        Guest,
        on_delete=models.PROTECT,
        related_name="voucher_orders",
        help_text="The guest who ordered the voucher",
    )

    is_sent = models.BooleanField(
        default=False,
        help_text="Check off once the voucher has been sent to the customer.",
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    _MAX_NUMBER_ATTEMPTS = 10

    @staticmethod
    def _generate_number():
        date_part = timezone.now().strftime("%Y%m%d")
        alphabet = string.digits
        for _ in range(VoucherOrder._MAX_NUMBER_ATTEMPTS):
            suffix = ''.join(secrets.choice(alphabet) for _ in range(6))
            number = f"V-{date_part}-{suffix}"
            if not VoucherOrder.objects.filter(number=number).exists():
                return number
        raise RuntimeError("Could not generate a unique voucher number after multiple attempts.")

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number
