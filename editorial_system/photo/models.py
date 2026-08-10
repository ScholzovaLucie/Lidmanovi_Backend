import os
import uuid

from django.db import models


def photo_upload_to(instance, filename):
    extension = os.path.splitext(filename)[1]
    safe_category = (instance.category or "uncategorized").strip().lower().replace(" ", "-")
    return f"editorial/photos/{safe_category}/{uuid.uuid4().hex}{extension}"


class Photo(models.Model):
    category = models.CharField(max_length=100, db_index=True)
    image = models.ImageField(upload_to=photo_upload_to)
    alt_text_i18n = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.category} #{self.id}"


class PhotoPlacement(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="placements")
    location = models.CharField(max_length=100, db_index=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["location", "order"]
        unique_together = [("photo", "location")]

    def __str__(self):
        return f"{self.location} → Photo #{self.photo_id} (order {self.order})"