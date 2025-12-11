from django.shortcuts import render

from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from editorial_system.iframe_embed.models import IframeEmbed
from editorial_system.iframe_embed.serializers import IframeEmbedSerializer


@extend_schema_view(
    list=extend_schema(tags=['Iframes Embed']),
    retrieve=extend_schema(tags=['Iframes Embed']),
    create=extend_schema(tags=['Iframes Embed']),
    update=extend_schema(tags=['Iframes Embed']),
    partial_update=extend_schema(tags=['Iframes Embed']),
    destroy=extend_schema(tags=['Iframes Embed'])
)
class IframeEmbedViewSet(viewsets.ModelViewSet):
    queryset = IframeEmbed.objects.all()
    serializer_class = IframeEmbedSerializer