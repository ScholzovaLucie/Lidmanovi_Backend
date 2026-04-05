from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

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
    permission_classes = [IsAdminUser]


@extend_schema_view(
    list=extend_schema(
        tags=["Info Boxes"],
        parameters=[
            OpenApiParameter(
                name="lang",
                type=OpenApiTypes.STR,
                required=False,
                description="Requested language (for example: cs, en, de).",
            ),
            OpenApiParameter(
                name="Accept-Language",
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.STR,
                required=False,
                description="Language preference header, used when lang query param is missing.",
            ),
        ],
        description="Return only info boxes that are currently active.",
        responses=InfoBoxSerializer(many=True),
    ),
)
class PublicInfoBoxViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = InfoBoxSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get"]

    def get_queryset(self):
        now = timezone.now()
        return InfoBox.objects.filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        ).order_by("id")
