from rest_framework import serializers

from pension.nearby_place.models import NearbyPlace


class NearbyPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NearbyPlace
        fields = [
            "id",
            "name",
            "link",
            "media_type",
            "media_url",
            "order",
            "is_active",
        ]