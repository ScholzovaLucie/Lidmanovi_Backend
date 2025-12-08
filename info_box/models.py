from django.db import models

class Audience(models.TextChoices):
    GUEST = "guest", "Guest"
    STAFF = "staff", "Staff"
    BOTH = "both", "Both"


class InfoBox(models.Model):
    title = models.CharField(max_length=200)
    content_json = models.JSONField(blank=True, null=True)

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    priority = models.IntegerField(default=0)
    audience = models.CharField(max_length=20, choices=Audience.choices)
    is_active = models.BooleanField(default=True)
