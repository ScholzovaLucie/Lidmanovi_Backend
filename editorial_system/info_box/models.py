from django.core.exceptions import ValidationError
from django.db import models


class InfoBox(models.Model):
    title_i18n = models.JSONField(default=dict, blank=True)
    content_json = models.JSONField(blank=True, null=True)

    starts_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Moment the info box becomes visible.",
    )
    ends_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Moment the info box stops being visible. For a single-day "
                   "info box, set this to the end of that day (e.g. 23:59), "
                   "not the same time as the start - otherwise it will never "
                   "be visible.",
    )

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError(
                "ends_at must be after starts_at, otherwise the info box "
                "will never be shown."
            )
