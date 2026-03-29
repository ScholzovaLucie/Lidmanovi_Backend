from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(
    {
        "type": "object",
        "additionalProperties": {"type": "string"},
        "example": {"cs": "Pokoj Komfort", "en": "Comfort Room"},
    }
)
class I18NTranslationsField(serializers.DictField):
    def __init__(self, **kwargs):
        kwargs.setdefault("child", serializers.CharField(allow_blank=True))
        kwargs.setdefault("required", False)
        kwargs.setdefault("default", dict)
        super().__init__(**kwargs)


@extend_schema_field(
    {
        "type": "object",
        "additionalProperties": True,
    }
)
class JSONObjectField(serializers.JSONField):
    pass
