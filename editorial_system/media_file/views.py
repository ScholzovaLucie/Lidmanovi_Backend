from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from editorial_system.media_file.models import MediaFile
from editorial_system.media_file.serializers import MediaFileSerializer


@extend_schema_view(
    list=extend_schema(tags=['Media Files']),
    retrieve=extend_schema(tags=['Media Files']),
    create=extend_schema(tags=['Media Files']),
    update=extend_schema(tags=['Media Files']),
    partial_update=extend_schema(tags=['Media Files']),
    destroy=extend_schema(tags=['Media Files'])
)
class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer