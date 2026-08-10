from rest_framework import serializers

from common.i18n import extract_requested_language
from common.schema import JSONObjectField
from editorial_system.page.models import Page, PageTranslation
from editorial_system.page.services import resolve_translation, TRANSLATION_MANUALLY_REVIEWED


class PageTranslationSerializer(serializers.ModelSerializer):
    content_json = JSONObjectField()

    class Meta:
        model = PageTranslation
        fields = ["id", "lang", "content_json", "state"]
        read_only_fields = ["id"]


class PageSerializer(serializers.ModelSerializer):
    content_json = JSONObjectField(help_text="Structured page content for the source language.")
    translations = PageTranslationSerializer(many=True, read_only=True)
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
            "translations",
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

        translation = resolve_translation(page=instance, requested_lang=normalized_requested_lang)

        if normalized_requested_lang == instance.lang:
            data["content_json"] = instance.content_json
            data["translation_status"] = "source_of_truth"
        elif translation is not None:
            data["content_json"] = translation.content_json
            data["translation_status"] = translation.state or "missing"
        else:
            data["content_json"] = instance.content_json
            data["translation_status"] = "missing"

        data["requested_lang"] = normalized_requested_lang

        is_public = not request or not getattr(request, "user", None) or not request.user.is_authenticated
        if is_public:
            data.pop("translations", None)

        return data