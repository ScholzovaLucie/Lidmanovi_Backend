from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from common.schema import I18NTranslationsField
from editorial_system.photo.models import Photo, PhotoPlacement


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    alt_text_i18n = I18NTranslationsField(help_text="Translated alt texts keyed by language code.")

    class Meta:
        model = Photo
        fields = ["id", "category", "url", "alt_text_i18n"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None

        relative_url = obj.image.url
        if request is None:
            return relative_url

        if relative_url.startswith("http"):
            return relative_url

        return request.build_absolute_uri(relative_url)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        language = extract_requested_language(request=request)

        data["alt_text"] = resolve_translated_value(
            base_value=None,
            translations=instance.alt_text_i18n,
            language=language,
        )
        return data


class PhotoUploadSerializer(serializers.ModelSerializer):
    alt_text_i18n = I18NTranslationsField(help_text="Translated alt texts keyed by language code.")

    class Meta:
        model = Photo
        fields = ["id", "category", "image", "alt_text_i18n"]
        read_only_fields = ["id"]


class PhotoUpdateSerializer(serializers.ModelSerializer):
    alt_text_i18n = I18NTranslationsField(help_text="Translated alt texts keyed by language code.")

    class Meta:
        model = Photo
        fields = ["id", "alt_text_i18n"]
        read_only_fields = ["id"]


class PhotoIdsRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class PhotoPlacementSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(read_only=True)
    photo_id = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), source="photo", write_only=True
    )

    class Meta:
        model = PhotoPlacement
        fields = ["id", "photo", "photo_id", "location", "order"]


class PhotoPlacementWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoPlacement
        fields = ["id", "photo", "location", "order"]
        read_only_fields = ["id"]