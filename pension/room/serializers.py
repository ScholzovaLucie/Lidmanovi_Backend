from rest_framework import serializers

from pension.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class RoomCombinationSerializer(serializers.Serializer):
    rooms_needed = serializers.IntegerField()
    capacity_total = serializers.IntegerField()
    rooms = RoomSerializer(many=True)