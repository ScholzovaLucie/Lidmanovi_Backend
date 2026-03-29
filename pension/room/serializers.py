from rest_framework import serializers

from common.i18n import extract_requested_language, resolve_translated_value
from common.schema import I18NTranslationsField
from pension.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    name_i18n = I18NTranslationsField(help_text="Translated room names keyed by language code.")
    description_i18n = I18NTranslationsField(help_text="Translated room descriptions keyed by language code.")

    class Meta:
        model = Room
        fields = [
            "id",
            "name",
            "name_i18n",
            "max_adults",
            "max_children",
            "capacity",
            "description",
            "description_i18n",
            "price_for_adult",
            "price_for_children",
            "is_active",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {"help_text": "Default room name, usually in the source language."},
            "description": {"help_text": "Default room description, usually in the source language."},
            "max_adults": {"help_text": "Maximum number of adults that fit into the room."},
            "max_children": {"help_text": "Maximum number of children that fit into the room."},
            "capacity": {"help_text": "Maximum total guest capacity for the room."},
            "price_for_adult": {"help_text": "Per-night price for one adult in CZK."},
            "price_for_children": {"help_text": "Per-night price for one child in CZK."},
            "is_active": {"help_text": "Whether the room can be offered in reservations."},
        }


class PublicRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "id",
            "name",
            "max_adults",
            "max_children",
            "capacity",
            "description",
            "price_for_adult",
            "price_for_children",
            "is_active",
        ]
        read_only_fields = fields

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
    people_total = serializers.IntegerField(help_text="Total requested number of guests.")
    mode = serializers.ChoiceField(
        choices=["single_room", "multiple_rooms"],
        help_text="Whether one room is enough or multiple rooms are needed.",
    )
    rooms = PublicRoomSerializer(many=True, help_text="Matching available rooms.")


class RoomAvailabilitySerializer(serializers.Serializer):
    room_id = serializers.IntegerField(help_text="Room ID that was checked.")
    available = serializers.BooleanField(help_text="Whether the room is available for the requested dates and capacity.")
