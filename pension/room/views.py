from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, decorators
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from pension.reservation.models import Reservation
from pension.room.models import Room
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from pension.room.serializers import RoomSerializer, RoomCombinationSerializer


@extend_schema_view(
    list=extend_schema(tags=['Rooms']),
    retrieve=extend_schema(tags=['Rooms']),
)
class PublicRoomViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = []
    http_method_names = ['get']


    @extend_schema(
        tags=['Rooms'],
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
                description='Count of children',
            ),
        ],
        responses=RoomCombinationSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='available-rooms')
    def get_available_rooms(self, request):
        from itertools import combinations

        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        adults = int(request.query_params.get('adults', 1))
        children = int(request.query_params.get('children', 0))

        if not from_date or not to_date:
            return Response({"error": "from_date and to_date are required"}, status=400)

        if to_date <= from_date:
            return Response({"error": "to_date must be greater than from_date"}, status=400)

        total_people = adults + children

        reservations = Reservation.objects.filter(
            check_in_date__lte=to_date,
            check_out_date__gte=from_date,
        )

        reserved_ids = reservations.values_list('rooms__id', flat=True)

        rooms = self.get_queryset().exclude(id__in=reserved_ids)

        available_rooms = [
            r for r in rooms
            if r.is_free(from_date, to_date)
        ]

        if not available_rooms:
            return Response({"options": []})

        available_rooms.sort(
            key=lambda r: r.max_adults + r.max_children,
            reverse=True
        )

        MAX_ROOMS_TO_COMBINE = 6
        available_rooms = available_rooms[:MAX_ROOMS_TO_COMBINE]

        results = []

        for r_count in range(1, len(available_rooms) + 1):
            for combo in combinations(available_rooms, r_count):

                capacity = sum(r.capacity for r in combo)

                if capacity >= total_people:
                    serialized = RoomSerializer(combo, many=True).data

                    results.append({
                        "rooms_needed": r_count,
                        "capacity_total": capacity,
                        "rooms": serialized
                    })

            if results:
                break

        return Response({
            "people_total": total_people,
            "options": results
        })

    @extend_schema(
        tags=['Rooms'],
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
                description='Count of children',
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


@extend_schema_view(
    update=extend_schema(tags=['Rooms']),
)
class PrivateRoomViewSet(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminUser]

    http_method_names = ['put']

