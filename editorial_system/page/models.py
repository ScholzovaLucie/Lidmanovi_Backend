from django.db import models


class Page(models.Model):
    path = models.CharField(max_length=255, db_index=True)
    lang = models.CharField(max_length=16, default="cs", db_index=True)
    content_json = models.JSONField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["path", "lang"],
                name="editorial_page_path_lang_unique",
            )
        ]


class PageTranslation(models.Model):
    page = models.ForeignKey(Page, related_name="translations", on_delete=models.CASCADE)
    lang = models.CharField(max_length=16, db_index=True)
    content_json = models.JSONField()
    state = models.CharField(max_length=64, default="", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["page", "lang"],
                name="editorial_pagetranslation_page_lang_unique",
            )
        ]
