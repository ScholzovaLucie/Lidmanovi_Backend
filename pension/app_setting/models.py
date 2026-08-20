from django.db import models


class AppSetting(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(null=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key
