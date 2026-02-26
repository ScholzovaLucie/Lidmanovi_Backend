from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from editorial_system.iframe_embed.models import IframeEmbed


class IframeEmbedSerializer(serializers.ModelSerializer):
    class Meta:
        model = IframeEmbed
        fields = '__all__'

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
