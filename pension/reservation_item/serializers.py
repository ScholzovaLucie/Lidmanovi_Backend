from rest_framework import serializers

from pension.reservation_item.models import ReservationItem


class ReservationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationItem
        fields = '__all__'