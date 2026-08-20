from django.db import models


class NearbyPlace(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Obrázek"
        IFRAME = "iframe", "Iframe"

    name = models.CharField(max_length=150)
    link = models.URLField(help_text="Odkaz na dané místo (web, Google Maps apod.).")
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)
    media_url = models.URLField(help_text="Adresa obrázku, nebo URL pro vložení do iframe.")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name