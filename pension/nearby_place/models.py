from django.db import models


class NearbyPlace(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Obrázek"
        IFRAME = "iframe", "Iframe"

    name = models.CharField(max_length=150)
    name_i18n = models.JSONField(default=dict, blank=True)
    link = models.URLField(
        max_length=2000,
        help_text="Odkaz na dané místo (web, Google Maps apod.).",
    )
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)
    media_url = models.URLField(
        max_length=2000,
        blank=True,
        help_text=(
            "URL pro vložení do iframe (jen media_type='iframe'). "
            "Pro media_type='image' se ignoruje – obrázek se řeší přes photo placement "
            "systém (location=f'nearby-place-{id}')."
        ),
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if isinstance(self.name_i18n, dict) and self.name_i18n.get("cs"):
            self.name = self.name_i18n["cs"]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name