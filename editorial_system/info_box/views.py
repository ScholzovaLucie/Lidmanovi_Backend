from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import viewsets

from editorial_system.info_box.models import InfoBox
from editorial_system.info_box.serializers import InfoBoxSerializer


@extend_schema_view(
    list=extend_schema(
        tags=['Info Boxes'],
        parameters=[
            OpenApiParameter(
                name='lang',
                type=OpenApiTypes.STR,
                required=False,
                description='Requested language (for example: cs, en, de).',
            ),
            OpenApiParameter(
                name='Accept-Language',
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.STR,
                required=False,
                description='Language preference header, used when lang query param is missing.',
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=['Info Boxes'],
        parameters=[
            OpenApiParameter(
                name='lang',
                type=OpenApiTypes.STR,
                required=False,
                description='Requested language (for example: cs, en, de).',
            ),
            OpenApiParameter(
                name='Accept-Language',
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.STR,
                required=False,
                description='Language preference header, used when lang query param is missing.',
            ),
        ],
    ),
    create=extend_schema(tags=['Info Boxes'], request=InfoBoxSerializer, responses=InfoBoxSerializer),
    update=extend_schema(tags=['Info Boxes'], request=InfoBoxSerializer, responses=InfoBoxSerializer),
    partial_update=extend_schema(tags=['Info Boxes'], request=InfoBoxSerializer, responses=InfoBoxSerializer),
    destroy=extend_schema(tags=['Info Boxes']),
)
class InfoBoxViewSet(viewsets.ModelViewSet):
    queryset = InfoBox.objects.all()
    serializer_class = InfoBoxSerializer
