from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from pension.amenity.models import AmenityIcon
from pension.amenity.serializers import AmenityIconSerializer


@extend_schema_view(
    list=extend_schema(tags=['Amenity Icons']),
    create=extend_schema(tags=['Amenity Icons']),
    partial_update=extend_schema(tags=['Amenity Icons']),
    destroy=extend_schema(tags=['Amenity Icons']),
)
class AmenityIconViewSet(viewsets.ModelViewSet):
    queryset = AmenityIcon.objects.all()
    serializer_class = AmenityIconSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None

    http_method_names = ['get', 'post', 'patch', 'delete']