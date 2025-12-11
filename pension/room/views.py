from rest_framework import viewsets

from pension.room.models import Room
from drf_spectacular.utils import extend_schema_view, extend_schema

from pension.room.serializers import RoomSerializer


@extend_schema_view(
    list=extend_schema(tags=['Rooms']),
    retrieve=extend_schema(tags=['Rooms']),
    create=extend_schema(tags=['Rooms']),
    update=extend_schema(tags=['Rooms']),
    partial_update=extend_schema(tags=['Rooms']),
    destroy=extend_schema(tags=['Rooms'])
)
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
