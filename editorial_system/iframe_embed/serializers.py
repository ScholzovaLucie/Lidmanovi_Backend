from rest_framework import serializers

from editorial_system.iframe_embed.models import IframeEmbed


class IframeEmbedSerializer(serializers.ModelSerializer):
    class Meta:
        model = IframeEmbed
        fields = '__all__'