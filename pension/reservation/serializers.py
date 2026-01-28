from rest_framework import serializers
from pension.reservation.models import Reservation
from pension.reservation_item.models import ReservationItem


class ReservationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'id',
            'check_in_date',
            'check_out_date',
            'status',
            'num_adults',
            'num_children',
            'note',
            'price',
            'currency',
            'primary_guest',
            'room',
            'items',
        ]


class ReservationCreateSerializer(serializers.ModelSerializer):
    items = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ReservationItem.objects.all()
    )

    class Meta:
        model = Reservation
        fields = [
            'check_in_date',
            'check_out_date',
            'num_adults',
            'num_children',
            'note',
            'currency',
            'primary_guest',
            'room',
            'items',
        ]


class ReservationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'check_in_date',
            'check_out_date',
            'num_adults',
            'num_children',
            'note',
            'room',
        ]



