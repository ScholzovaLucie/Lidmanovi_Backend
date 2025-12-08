from django.db import models

class PageStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class Page(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)

    content_json = models.JSONField(blank=True, null=True)
    seo_json = models.JSONField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=PageStatus.choices,
        default=PageStatus.DRAFT
    )

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
