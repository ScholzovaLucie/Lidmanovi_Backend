from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from pension.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class PublicRoomSerializer(RoomSerializer):
    class Meta:
        model = Room
        exclude = ['name_i18n', 'description_i18n']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        language = extract_requested_language(request=request)

        data["name"] = resolve_translated_value(
            base_value=instance.name,
            translations=instance.name_i18n,
            language=language,
        )
        data["description"] = resolve_translated_value(
            base_value=instance.description,
            translations=instance.description_i18n,
            language=language,
        )
        return data


class RoomCombinationSerializer(serializers.Serializer):
    people_total = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["single_room", "multiple_rooms"])
    rooms = PublicRoomSerializer(many=True)
