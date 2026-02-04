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


class SendEmailResponseSerializer(serializers.Serializer):
    status = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()