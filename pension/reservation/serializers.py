from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
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

        if not room.is_active:
            raise serializers.ValidationError("Room is not active")

        if not room.can_fit(data['num_adults'], data['num_children']):
            raise serializers.ValidationError("Room does not have enough capacity")

        return data


class ReservationCreateSerializer(serializers.ModelSerializer):
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Frontend alias for reservation note.",
    )
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
            'message',
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
        if not data.get("note") and data.get("message") is not None:
            data["note"] = data["message"]

        if data['check_out_date'] <= data['check_in_date']:
            raise serializers.ValidationError(
                "check_out_date must be greater than check_in_date"
            )

        rooms = data.get("rooms") or []
        if not rooms:
            raise serializers.ValidationError({"rooms": ["At least one room must be selected."]})

        room_ids = [room["id"] for room in rooms]
        if len(room_ids) != len(set(room_ids)):
            raise serializers.ValidationError({"rooms": ["Each room can only be selected once."]})

        initial_data = getattr(self, "initial_data", {}) or {}
        has_explicit_num_adults = "num_adults" in initial_data
        has_explicit_num_children = "num_children" in initial_data
        explicit_num_adults = data.get("num_adults")
        explicit_num_children = data.get("num_children")
        rooms_num_adults = sum(room["num_adults"] for room in rooms)
        rooms_num_children = sum(room["num_children"] for room in rooms)

        if has_explicit_num_adults and explicit_num_adults != rooms_num_adults:
            raise serializers.ValidationError(
                {"num_adults": ["Total adults must match the sum of adults assigned to rooms."]}
            )

        if has_explicit_num_children and explicit_num_children != rooms_num_children:
            raise serializers.ValidationError(
                {"num_children": ["Total children must match the sum of children assigned to rooms."]}
            )

        return data

    def create(self, validated_data):
        with transaction.atomic():
            guest_data = validated_data.pop('primary_guest')
            rooms = validated_data.pop('rooms')
            validated_data.pop('message', None)

            guest = Guest.objects.filter(
                first_name__iexact=guest_data.get('first_name'),
                last_name__iexact=guest_data.get('last_name'),
                email__iexact=guest_data.get('email'),
            ).first()
            if guest is None:
                guest = Guest.objects.create(**guest_data)

            if not validated_data.get("num_adults"):
                validated_data['num_adults'] = sum(r['num_adults'] for r in rooms)

            if not validated_data.get("num_children"):
                validated_data['num_children'] = sum(r['num_children'] for r in rooms)

            reservation = Reservation(primary_guest=guest, **validated_data)

            try:
                reservation.validate_rooms(rooms, lock=True)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages)

            reservation.save()
            reservation.rooms.add(*[room_data['room'] for room_data in rooms])
            reservation.price = reservation.calculate_price(rooms)
            reservation.save(update_fields=['price'])

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
