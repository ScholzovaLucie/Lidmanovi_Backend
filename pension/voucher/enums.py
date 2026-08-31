from django.db import models


class VoucherStatus(models.TextChoices):
    NEW = "new", "New"
    CONFIRMED = "confirmed", "Confirmed"
    SENT = "sent", "Sent"
    CANCELLED = "cancelled", "Cancelled"