from django.db import transaction
from rest_framework import serializers

from pension.guest.models import Guest
from pension.guest.serializers import GuestSerializer
from pension.reservation.models import Reservation
from pension.room.models import Room
from pension.room.serializers import RoomSerializer


class ReservationReadSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True)
    primary_guest = GuestSerializer()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'number',
            'check_in_date',
            'check_out_date',
            'status',
            'num_adults',
            'num_children',
            'note',
            'price',
            'currency',
            'primary_guest',
            'rooms',
        ]


class ReservationGuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "country",
            "note",
        ]
        validators = []
        extra_kwargs = {
            "first_name": {"help_text": "Guest first name."},
            "last_name": {"help_text": "Guest last name."},
            "email": {"help_text": "Guest email address."},
            "phone": {"help_text": "Guest phone number."},
            "country": {"help_text": "Guest country."},
            "note": {"help_text": "Additional guest note."},
        }


class RoomReservationCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Room ID")
    num_adults = serializers.IntegerField(min_value=1, help_text="Number of adults assigned to this room.")
    num_children = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Number of children assigned to this room.",
    )

    def validate(self, data):
        try:
            room = Room.objects.get(id=data['id'])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room does not exist")

        if not room.can_fit(data['num_adults'], data['num_children']):
            raise serializers.ValidationError("Room does not have enough capacity")

        return data



class ReservationCreateSerializer(serializers.ModelSerializer):
    primary_guest = ReservationGuestSerializer(help_text="Guest who created reservation")
    rooms = RoomReservationCreateSerializer(many=True, help_text="Rooms reserved")
    num_adults = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Total adults in reservation. If omitted, it is calculated from rooms.",
    )
    num_children = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Total children in reservation. If omitted, it is calculated from rooms.",
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
            'rooms',
        ]
        extra_kwargs = {
            "check_in_date": {"help_text": "Reservation start date."},
            "check_out_date": {"help_text": "Reservation end date."},
            "note": {"help_text": "Optional reservation note."},
            "currency": {"help_text": "Reservation currency, for example CZK."},
        }

    def validate(self, data):
        if data['check_out_date'] <= data['check_in_date']:
            raise serializers.ValidationError(
                "check_out_date must be greater than check_in_date"
            )

        return data

    def create(self, validated_data):
        with transaction.atomic():
            guest_data = validated_data.pop('primary_guest')
            rooms = validated_data.pop('rooms')

            guest = Guest.objects.filter(
                first_name=guest_data.get('first_name'),
                last_name=guest_data.get('last_name'),
                email=guest_data.get('email'),
            ).first()
            if guest is None:
                guest = Guest.objects.create(**guest_data)

            if not validated_data.get("num_adults") or validated_data.get("num_adults") == 0:
                amount = 0
                for room in rooms:
                    amount += room['num_adults']
                validated_data['num_adults'] = amount

            if not validated_data.get("num_children") or validated_data.get("num_children") == 0:
                amount = 0
                for room in rooms:
                    amount += room['num_children']
                validated_data['num_children'] = amount

            reservation = Reservation.objects.create(
                primary_guest=guest,
                **validated_data
            )

            reservation.validate_rooms(rooms)
            for room in rooms:
                try:
                    room = Room.objects.get(id=room['id'])
                except Room.DoesNotExist:
                    raise serializers.ValidationError(f"Room {room['id']} does not exist.")
                reservation.rooms.add(room)

            reservation.price = reservation.calculate_price(rooms)
            reservation.save()

            return reservation


class ReservationUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=Reservation._meta.get_field('status').choices,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Reservation
        fields = [
            'status',
        ]



class ReservationCancelSerializer(serializers.ModelSerializer):
    cancel_reason = serializers.CharField(required=True)

    class Meta:
        model = Reservation
        fields = [
            'cancel_reason',
        ]


class ReservationStatusSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Reservation status machine value.")
    label = serializers.CharField(help_text="Reservation status human-readable label.")
