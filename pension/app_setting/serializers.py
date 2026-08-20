from rest_framework import serializers


class AppSettingSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=255, allow_blank=False, trim_whitespace=True)
    value = serializers.JSONField(allow_null=True)
