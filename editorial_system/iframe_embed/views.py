from django.shortcuts import render

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import viewsets

from editorial_system.iframe_embed.models import IframeEmbed
from editorial_system.iframe_embed.serializers import IframeEmbedSerializer


@extend_schema_view(
    list=extend_schema(
        tags=['Iframes Embed'],
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
        tags=['Iframes Embed'],
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
    create=extend_schema(tags=['Iframes Embed']),
    update=extend_schema(tags=['Iframes Embed']),
    partial_update=extend_schema(tags=['Iframes Embed']),
    destroy=extend_schema(tags=['Iframes Embed'])
)
class IframeEmbedViewSet(viewsets.ModelViewSet):
    queryset = IframeEmbed.objects.all()
    serializer_class = IframeEmbedSerializer
