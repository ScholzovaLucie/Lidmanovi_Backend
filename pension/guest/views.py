from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets

from pension.guest.models import Guest
from pension.guest.serializers import GuestSerializer


# Create your views here.
@extend_schema_view(
    list=extend_schema(tags=['Guests']),
    retrieve=extend_schema(tags=['Guests']),
    create=extend_schema(tags=['Guests']),
    update=extend_schema(tags=['Guests']),
    partial_update=extend_schema(tags=['Guests']),
    destroy=extend_schema(tags=['Guests']),
)
class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
