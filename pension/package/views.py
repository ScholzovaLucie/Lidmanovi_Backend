from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from pension.package.models import Package
from pension.package.serializers import PackageSerializer


@extend_schema_view(
    list=extend_schema(tags=['Packages']),
    retrieve=extend_schema(tags=['Packages']),
    create=extend_schema(tags=['Packages']),
    update=extend_schema(tags=['Packages']),
    partial_update=extend_schema(tags=['Packages']),
    destroy=extend_schema(tags=['Packages'])
)
class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer