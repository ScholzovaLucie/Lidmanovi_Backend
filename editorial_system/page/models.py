from django.db import models


class Page(models.Model):
    content_json = models.JSONField(blank=True, null=True)
