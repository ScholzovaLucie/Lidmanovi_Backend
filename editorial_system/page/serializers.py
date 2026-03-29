from rest_framework import serializers

from common.i18n import extract_requested_language
from common.schema import JSONObjectField
from editorial_system.page.models import Page
from editorial_system.page.services import get_translated_content


class PageSerializer(serializers.ModelSerializer):
    content_json = JSONObjectField(help_text="Structured page content for the source language.")
    content_i18n = JSONObjectField(help_text="Translated page content keyed by language code.", required=False)
    translation_state_i18n = JSONObjectField(
        help_text="Translation metadata keyed by language code.",
        required=False,
    )
    translation_status = serializers.CharField(
        read_only=True,
        help_text="Computed status for the requested language.",
    )
    requested_lang = serializers.CharField(
        read_only=True,
        help_text="Language actually used to build the response.",
    )

    def validate_lang(self, value):
        return value.strip().lower()

    def validate_path(self, value):
        normalized_path = value.strip()
        if not normalized_path:
            raise serializers.ValidationError("This field may not be blank.")
        if not normalized_path.startswith("/"):
            normalized_path = f"/{normalized_path}"
        return normalized_path

    class Meta:
        model = Page
        fields = [
            "id",
            "path",
            "lang",
            "content_json",
            "content_i18n",
            "translation_state_i18n",
            "translation_status",
            "requested_lang",
        ]
        read_only_fields = ["id", "translation_status", "requested_lang"]
        extra_kwargs = {
            "path": {"help_text": "Page route path, for example /kontakt."},
            "lang": {"help_text": "Source language of this page record."},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        requested_lang = extract_requested_language(request=request, default_language=instance.lang)
        normalized_requested_lang = (requested_lang or instance.lang).strip().lower()

        data["content_json"] = get_translated_content(
            page=instance,
            requested_lang=normalized_requested_lang,
        )

        if normalized_requested_lang == instance.lang:
            data["translation_status"] = "source_of_truth"
        else:
            state_map = instance.translation_state_i18n or {}
            state = state_map.get(normalized_requested_lang, {}).get("state")
            data["translation_status"] = state or "missing"

        data["requested_lang"] = normalized_requested_lang

        is_public = not request or not getattr(request, "user", None) or not request.user.is_authenticated
        if is_public:
            data.pop("content_i18n", None)
            data.pop("translation_state_i18n", None)

        return data
