from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from editorial_system.page.models import Page
from editorial_system.page.serializers import PageSerializer


@extend_schema_view(
    list=extend_schema(tags=['Pages']),
    retrieve=extend_schema(tags=['Pages']),
    create=extend_schema(tags=['Pages']),
    update=extend_schema(tags=['Pages']),
    partial_update=extend_schema(tags=['Pages']),
    destroy=extend_schema(tags=['Pages'])
)
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer