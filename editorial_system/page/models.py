from django.db import models


class Page(models.Model):
    path = models.CharField(max_length=255, db_index=True)
    lang = models.CharField(max_length=16, default="cs", db_index=True)
    content_json = models.JSONField(blank=True, null=True)
    content_i18n = models.JSONField(default=dict, blank=True)
    translation_state_i18n = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["path", "lang"],
                name="editorial_page_path_lang_unique",
            )
        ]
