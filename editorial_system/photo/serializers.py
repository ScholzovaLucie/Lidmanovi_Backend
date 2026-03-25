from rest_framework import serializers

from editorial_system.photo.models import Photo


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ["id", "category", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None

        relative_url = obj.image.url
        if request is None:
            return relative_url

        return request.build_absolute_uri(relative_url)


class PhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["id", "category", "image"]
        read_only_fields = ["id"]


class PhotoIdsRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
