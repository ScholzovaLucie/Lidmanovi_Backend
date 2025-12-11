from django.db import models


class MediaFile(models.Model):
    file_url = models.TextField()
    alt_text = models.CharField(max_length=255, blank=True)
    meta_json = models.JSONField(blank=True, null=True)
