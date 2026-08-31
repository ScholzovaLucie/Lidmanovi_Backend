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
    email = serializers.EmailField(help_text="Guest email address.")

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
            'status',
            'amount',
            'currency',
            'delivery_method',
            'shipping_street',
            'shipping_house_number',
            'shipping_city',
            'shipping_postal_code',
            'shipping_country',
            'note',
            'guest',
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
            'delivery_method',
            'shipping_street',
            'shipping_house_number',
            'shipping_city',
            'shipping_postal_code',
            'shipping_country',
            'note',
        ]
        extra_kwargs = {
            "delivery_method": {"help_text": "Whether the voucher should be sent by email or in printed form."},
            "shipping_street": {"help_text": "Street name. Required when delivery_method is 'print'."},
            "shipping_house_number": {"help_text": "House number. Required when delivery_method is 'print'."},
            "shipping_city": {"help_text": "City. Required when delivery_method is 'print'."},
            "shipping_postal_code": {"help_text": "Postal code. Required when delivery_method is 'print'."},
            "shipping_country": {"help_text": "Country. Required when delivery_method is 'print'."},
            "note": {"help_text": "Optional note for the voucher order."},
        }

    def validate(self, data):
        delivery_method = data.get('delivery_method') or VoucherOrder.DeliveryMethod.EMAIL
        if delivery_method == VoucherOrder.DeliveryMethod.PRINT:
            address_fields = [
                'shipping_street',
                'shipping_house_number',
                'shipping_city',
                'shipping_postal_code',
                'shipping_country',
            ]
            errors = {
                field: ["This field is required when delivery_method is 'print'."]
                for field in address_fields
                if not data.get(field)
            }
            if errors:
                raise serializers.ValidationError(errors)

        return data

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


class VoucherOrderUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=VoucherOrder._meta.get_field('status').choices,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = VoucherOrder
        fields = [
            'status',
        ]


class VoucherOrderStatusSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Voucher order status machine value.")
    label = serializers.CharField(help_text="Voucher order status human-readable label.")
