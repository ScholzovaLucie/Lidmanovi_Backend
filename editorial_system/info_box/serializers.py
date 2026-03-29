from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from common.schema import I18NTranslationsField, JSONObjectField
from editorial_system.info_box.models import InfoBox


class InfoBoxSerializer(serializers.ModelSerializer):
    title_i18n = I18NTranslationsField(help_text="Translated titles keyed by language code.")
    content_json = JSONObjectField(help_text="Structured info box content payload.")

    class Meta:
        model = InfoBox
        fields = [
            "id",
            "title",
            "title_i18n",
            "content_json",
            "starts_at",
            "ends_at",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "title": {"help_text": "Default info box title in the source language."},
            "starts_at": {"help_text": "Optional start date-time when the info box becomes visible."},
            "ends_at": {"help_text": "Optional end date-time when the info box stops being visible."},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        language = extract_requested_language(request=request)

        data["title"] = resolve_translated_value(
            base_value=instance.title,
            translations=instance.title_i18n,
            language=language,
        )
        return data
