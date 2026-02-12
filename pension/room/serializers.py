from rest_framework import serializers

from pension.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class RoomCombinationSerializer(serializers.Serializer):
    people_total = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["single_room", "multiple_rooms"])
    rooms = RoomSerializer(many=True)