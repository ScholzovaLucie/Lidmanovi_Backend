from rest_framework import serializers

from pension.guest.models import Guest
from pension.guest.serializers import GuestSerializer
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
    primary_guest = GuestSerializer(help_text="Guest who created reservation")

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

    def validate(self, data):
        if data['check_out_date'] <= data['check_in_date']:
            raise serializers.ValidationError(
                "check_out_date must be greater than check_in_date"
            )

        room = data['room']
        from_date = data['check_in_date']
        to_date = data['check_out_date']
        people = data['num_adults']
        children = data['num_children']

        if not room.is_available(from_date, to_date, people, children):
            raise serializers.ValidationError(
                "Room is not available for selected dates or capacity."
            )

        return data

    def create(self, validated_data):
        guest_data = validated_data.pop('primary_guest')
        items = validated_data.pop('items')

        guest, _ = Guest.objects.get_or_create(
            email=guest_data.get('email'),
            document_number=guest_data.get('document_number'),
            defaults=guest_data
        )

        reservation = Reservation.objects.create(
            primary_guest=guest,
            **validated_data
        )

        reservation.items.set(items)

        return reservation


class ReservationUpdateSerializer(serializers.ModelSerializer):
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.ChoiceField(
        choices=Reservation._meta.get_field('status').choices,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Reservation
        fields = [
            'note',
            'status',
        ]

