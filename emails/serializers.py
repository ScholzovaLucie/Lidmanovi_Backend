from rest_framework import serializers

from emails.constants import EmailType


class SendEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField()
    message = serializers.CharField()
    type = serializers.ChoiceField(choices=EmailType.CHOICES)

    recipient_name = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    persons = serializers.IntegerField(help_text="Number of persons")
    reason = serializers.CharField(help_text="Reason")

    def validate(self, attrs):
        to_date = attrs["date_to"]
        from_date = attrs["date_from"]
        if to_date <= from_date:
            raise serializers.ValidationError("to_date must be greater than from_date")

        return attrs


class SendEmailResponseSerializer(serializers.Serializer):
    status = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()