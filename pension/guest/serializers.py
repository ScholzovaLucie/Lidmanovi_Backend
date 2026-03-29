from rest_framework import serializers

from pension.guest.models import Guest


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "country",
            "note",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {"help_text": "Guest first name."},
            "last_name": {"help_text": "Guest last name."},
            "email": {"help_text": "Guest email address."},
            "phone": {"help_text": "Guest phone number."},
            "country": {"help_text": "Guest country."},
            "note": {"help_text": "Internal or booking note related to the guest."},
        }
