from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from editorial_system.info_box.models import InfoBox
from editorial_system.info_box.serializers import InfoBoxSerializer


@extend_schema_view(
    list=extend_schema(tags=['Info Boxes']),
    retrieve=extend_schema(tags=['Info Boxes']),
    create=extend_schema(tags=['Info Boxes']),
    update=extend_schema(tags=['Info Boxes']),
    partial_update=extend_schema(tags=['Info Boxes']),
    destroy=extend_schema(tags=['Info Boxes']),
)
class InfoBoxViewSet(viewsets.ModelViewSet):
    queryset = InfoBox.objects.all()
    serializer_class = InfoBoxSerializer
