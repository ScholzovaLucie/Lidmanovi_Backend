import secrets
import string

from django.db import models
from django.utils import timezone

from pension.guest.models import Guest
from pension.voucher.enums import VoucherStatus


STATUS_MAP_TO_MAIL = {
    VoucherStatus.CONFIRMED: "voucher_order_confirmed",
    VoucherStatus.SENT: "voucher_order_sent",
    VoucherStatus.CANCELLED: "voucher_order_cancelled",
}


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
    class DeliveryMethod(models.TextChoices):
        EMAIL = "email", "E-mail"
        PRINT = "print", "Tištěná podoba"

    created_at = models.DateTimeField(auto_now_add=True)

    number = models.CharField(max_length=20, unique=True)

    status = models.CharField(
        max_length=20,
        choices=VoucherStatus.choices,
        default=VoucherStatus.NEW,
        db_index=True,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="CZK")

    delivery_method = models.CharField(
        max_length=10,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.EMAIL,
        help_text="Whether the voucher should be sent by email or in printed form.",
    )

    shipping_street = models.CharField(max_length=255, blank=True)
    shipping_house_number = models.CharField(max_length=20, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)

    note = models.TextField(blank=True)

    guest = models.ForeignKey(
        Guest,
        on_delete=models.PROTECT,
        related_name="voucher_orders",
        help_text="The guest who ordered the voucher",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the voucher order status was set to 'sent'.",
    )

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

    @property
    def full_shipping_address(self):
        if not self.shipping_street:
            return ""
        return (
            f"{self.shipping_street} {self.shipping_house_number}, "
            f"{self.shipping_postal_code} {self.shipping_city}, {self.shipping_country}"
        )

    def __str__(self):
        return self.number
