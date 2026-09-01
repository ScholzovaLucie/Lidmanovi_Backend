from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from pension.nearby_place.models import NearbyPlace
from pension.nearby_place.serializers import NearbyPlaceSerializer


@extend_schema_view(
    list=extend_schema(tags=["Nearby Places"]),
)
class PublicNearbyPlaceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = NearbyPlace.objects.filter(is_active=True)
    serializer_class = NearbyPlaceSerializer
    permission_classes = []
    pagination_class = None
    http_method_names = ["get"]


@extend_schema_view(
    list=extend_schema(tags=["Nearby Places"]),
    create=extend_schema(tags=["Nearby Places"]),
    partial_update=extend_schema(tags=["Nearby Places"]),
    destroy=extend_schema(tags=["Nearby Places"]),
)
class AdminNearbyPlaceViewSet(viewsets.ModelViewSet):
    queryset = NearbyPlace.objects.all()
    serializer_class = NearbyPlaceSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    http_method_names = ["get", "post", "put", "patch", "delete"]