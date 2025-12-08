from django.db import models

from page.models import Page


class MediaFile(models.Model):
    file_url = models.TextField()
    alt_text = models.CharField(max_length=255, blank=True)
    meta_json = models.JSONField(blank=True, null=True)

    page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL)
