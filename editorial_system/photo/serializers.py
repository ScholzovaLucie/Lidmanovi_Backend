from rest_framework import serializers

from editorial_system.photo.models import Photo, PhotoPlacement


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ["id", "category", "url", "alt_text"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None

        relative_url = obj.image.url
        if request is None:
            return relative_url

        if relative_url.startswith("http"):
            return relative_url

        return request.build_absolute_uri(relative_url)


class PhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["id", "category", "image", "alt_text"]
        read_only_fields = ["id"]


class PhotoIdsRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class PhotoPlacementSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(read_only=True)
    photo_id = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), source="photo", write_only=True
    )

    class Meta:
        model = PhotoPlacement
        fields = ["id", "photo", "photo_id", "location", "order"]


class PhotoPlacementWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoPlacement
        fields = ["id", "photo", "location", "order"]
        read_only_fields = ["id"]