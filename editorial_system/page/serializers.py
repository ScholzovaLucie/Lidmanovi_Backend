from rest_framework import serializers

from editorial_system.page.models import Page


class PageSerializer(serializers.ModelSerializer):
    def validate_lang(self, value):
        return value.strip().lower()

    def validate_path(self, value):
        normalized_path = value.strip()
        if not normalized_path:
            raise serializers.ValidationError("This field may not be blank.")
        if not normalized_path.startswith("/"):
            normalized_path = f"/{normalized_path}"
        return normalized_path

    class Meta:
        model = Page
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
        }
