from rest_framework import serializers

from common.schema import I18NTranslationsField
from editorial_system.photo.models import PhotoPlacement
from editorial_system.photo.serializers import PhotoSerializer
from pension.nearby_place.models import NearbyPlace


class NearbyPlaceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        read_only=True,
        help_text="Derived from name_i18n['cs'] on save; not accepted as input.",
    )
    name_i18n = I18NTranslationsField(help_text="Translated names keyed by language code (cs, en, pl, de).")
    media_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text=(
            "URL pro vložení do iframe. Povinné pouze pro media_type='iframe'. "
            "Pro media_type='image' je ignorováno – obrázek se čte z photo placement "
            "systému (location=f'nearby-place-{id}') a v odpovědi je doplněn automaticky."
        ),
    )

    class Meta:
        model = NearbyPlace
        fields = [
            "id",
            "name",
            "name_i18n",
            "link",
            "media_type",
            "media_url",
            "order",
            "is_active",
        ]

    def validate(self, data):
        media_type = data.get("media_type", getattr(self.instance, "media_type", NearbyPlace.MediaType.IMAGE))
        if media_type == NearbyPlace.MediaType.IFRAME and not data.get("media_url"):
            raise serializers.ValidationError(
                {"media_url": ["This field is required when media_type is 'iframe'."]}
            )
        return data

    def create(self, validated_data):
        if validated_data.get("media_type", NearbyPlace.MediaType.IMAGE) == NearbyPlace.MediaType.IMAGE:
            validated_data["media_url"] = ""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        media_type = validated_data.get("media_type", instance.media_type)
        if media_type == NearbyPlace.MediaType.IMAGE:
            validated_data["media_url"] = ""
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.media_type == NearbyPlace.MediaType.IMAGE:
            placement = (
                PhotoPlacement.objects.filter(location=f"nearby-place-{instance.id}")
                .select_related("photo")
                .order_by("order")
                .first()
            )
            photo_serializer = PhotoSerializer(context=self.context)
            data["media_url"] = photo_serializer.get_url(placement.photo) if placement else None
        return data