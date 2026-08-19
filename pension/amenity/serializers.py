import re

from rest_framework import serializers

from pension.amenity.models import AmenityIcon


class AmenityIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmenityIcon
        fields = ["id", "key", "label", "order", "is_active"]

    def validate_key(self, value):
        if not re.match(r"^[a-z0-9_-]+$", value):
            raise serializers.ValidationError(
                "key smí obsahovat jen malá písmena, číslice, pomlčku a podtržítko."
            )
        return value