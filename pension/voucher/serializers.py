from rest_framework import serializers

from pension.guest.models import Guest
from pension.guest.serializers import GuestSerializer
from pension.voucher.models import VoucherAmount, VoucherOrder


class VoucherAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherAmount
        fields = [
            'id',
            'value',
            'currency',
        ]


class VoucherGuestSerializer(serializers.ModelSerializer):
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


class VoucherOrderReadSerializer(serializers.ModelSerializer):
    guest = GuestSerializer()

    class Meta:
        model = VoucherOrder
        fields = [
            'id',
            'number',
            'created_at',
            'amount',
            'currency',
            'note',
            'guest',
            'is_sent',
            'sent_at',
        ]


class VoucherOrderCreateSerializer(serializers.ModelSerializer):
    guest = VoucherGuestSerializer(help_text="Guest who is ordering the voucher.")
    amount_id = serializers.PrimaryKeyRelatedField(
        queryset=VoucherAmount.objects.filter(is_active=True),
        source="amount_choice",
        write_only=True,
        help_text="ID of the selected voucher amount option.",
    )

    class Meta:
        model = VoucherOrder
        fields = [
            'guest',
            'amount_id',
            'note',
        ]
        extra_kwargs = {
            "note": {"help_text": "Optional note for the voucher order."},
        }

    def create(self, validated_data):
        guest_data = validated_data.pop('guest')
        amount_choice = validated_data.pop('amount_choice')

        guest = Guest.objects.filter(
            first_name__iexact=guest_data.get('first_name'),
            last_name__iexact=guest_data.get('last_name'),
            email__iexact=guest_data.get('email'),
        ).first()
        if guest is None:
            guest = Guest.objects.create(**guest_data)

        return VoucherOrder.objects.create(
            guest=guest,
            amount=amount_choice.value,
            currency=amount_choice.currency,
            **validated_data,
        )
