from django.utils import timezone
from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from common.schema import I18NTranslationsField, JSONObjectField
from editorial_system.info_box.models import InfoBox


class InfoBoxSerializer(serializers.ModelSerializer):
    title_i18n = I18NTranslationsField(help_text="Translated titles keyed by language code.")
    content_json = JSONObjectField(help_text="Structured info box content payload.")
    is_active = serializers.SerializerMethodField(help_text="True if the info box is currently within its active date range.")

    class Meta:
        model = InfoBox
        fields = [
            "id",
            "title_i18n",
            "content_json",
            "starts_at",
            "ends_at",
            "is_active",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "starts_at": {"help_text": "Optional start date-time when the info box becomes visible."},
            "ends_at": {
                "help_text": "Optional end date-time when the info box stops being visible. "
                              "For a single-day info box, set this to the end of that day "
                              "(e.g. 23:59), not the same time as starts_at."
            },
        }

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                "ends_at must be after starts_at, otherwise the info box will never be shown."
            )
        return attrs

    def get_is_active(self, instance):
        # Kept in sync with PublicInfoBoxViewSet.get_queryset's starts_at/ends_at filtering.
        now = timezone.now()
        if instance.starts_at and now < instance.starts_at:
            return False
        if instance.ends_at and now > instance.ends_at:
            return False
        return True

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        language = extract_requested_language(request=request)

        data["title"] = resolve_translated_value(
            base_value=None,
            translations=instance.title_i18n,
            language=language,
        )
        return data
