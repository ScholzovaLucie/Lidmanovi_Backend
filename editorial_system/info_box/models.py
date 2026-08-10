from django.db import models


class InfoBox(models.Model):
    title_i18n = models.JSONField(default=dict, blank=True)
    content_json = models.JSONField(blank=True, null=True)

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
