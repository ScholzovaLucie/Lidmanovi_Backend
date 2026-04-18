from rest_framework import serializers

from emails.constants import EmailType


class SendEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField()
    type = serializers.ChoiceField(choices=EmailType.CHOICES)

    recipient_name = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    persons = serializers.IntegerField(required=False, allow_null=True, help_text="Number of persons")
    reason = serializers.CharField(required=False, allow_blank=True, help_text="Reason")

    def validate(self, attrs):
        from_date = attrs.get("date_from")
        to_date = attrs.get("date_to")
        if from_date and to_date and to_date <= from_date:
            raise serializers.ValidationError("date_to must be greater than date_from")
        return attrs


class SendEmailResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
