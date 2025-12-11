from django.db import models

from editorial_system.page.models import Page


class IframeEmbed(models.Model):
    title = models.CharField(max_length=200, blank=True)
    url = models.TextField()
    settings_json = models.JSONField(blank=True, null=True)