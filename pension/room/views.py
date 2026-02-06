from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, decorators
from rest_framework.response import Response

from pension.reservation.models import Reservation
from pension.room.models import Room
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from pension.room.serializers import RoomSerializer


@extend_schema_view(
    list=extend_schema(tags=['Rooms']),
    retrieve=extend_schema(tags=['Rooms']),
)
class RoomViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    @extend_schema(
        tags=['Reservations'],
        parameters=[
            OpenApiParameter(
                name='from_date',
                type=OpenApiTypes.DATE,
                required=True,
                description='Start date (YYYY-MM-DD)',
            ),
            OpenApiParameter(
                name='to_date',
                type=OpenApiTypes.DATE,
                required=True,
                description='End date (YYYY-MM-DD)',
            ),
        ],
        responses=RoomSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='by-date')
    def get_rooms_by_date(self, request):
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        reservations = Reservation.objects.filter(
            check_in_date__lte=to_date,
            check_out_date__gte=from_date,
        )
        rooms_in_reservations = reservations.values_list('room', flat=True)

        serializer = RoomSerializer(rooms_in_reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Reservations'],
        parameters=[
            OpenApiParameter(
                name='from_date',
                type=OpenApiTypes.DATE,
                required=True,
                description='Start date (YYYY-MM-DD)',
            ),
            OpenApiParameter(
                name='to_date',
                type=OpenApiTypes.DATE,
                required=True,
                description='End date (YYYY-MM-DD)',
            ),
            OpenApiParameter(
                name='adults',
                type=OpenApiTypes.INT,
                required=True,
                description='Count of adults',
            ),
            OpenApiParameter(
                name='children',
                type=OpenApiTypes.INT,
                required=True,
                description='Count of childrens',
            ),
        ],
        responses=RoomSerializer(many=True),
    )
    @decorators.action(detail=True, methods=['get'], url_path='availability')
    def check_availability(self, request, pk=None):
        room = self.get_object()

        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        adults = int(request.query_params.get('adults', 1))
        children = int(request.query_params.get('children', 0))

        if not from_date or not to_date:
            return Response({"error": "from_date and to_date are required"}, status=400)
        if adults < 1:
            return Response({"error": "adults must be at least 1"}, status=400)
        if children < 0:
            return Response({"error": "children must be at least 0"}, status=400)

        if to_date <= from_date:
            return Response({"error": "to_date must be greater than from_date"},status=400)


        available = room.is_available(from_date, to_date, adults, children)

        return Response({
            "room_id": room.id,
            "available": available
        })