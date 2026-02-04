from django.db import models


class ReservationStatus(models.TextChoices):
    NEW = "new", "New"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    PAYMENT_PENDING = "payment_pending", "Payment pending"
    PAYED = "payed", "Payed"
    DONE = "done", "Done"
