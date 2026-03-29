from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, decorators
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils.dateparse import parse_date

from pension.reservation.models import Reservation
from pension.room.models import Room
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from pension.room.serializers import (
    RoomAvailabilitySerializer,
    RoomCombinationSerializer,
    RoomSerializer,
    PublicRoomSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Rooms'],
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
        tags=['Rooms'],
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
)
class PublicRoomViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Room.objects.all()
    serializer_class = PublicRoomSerializer
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
        responses=RoomCombinationSerializer,
    )
    @decorators.action(detail=False, methods=['get'], url_path='available-rooms')
    def get_available_rooms(self, request):
        from_date_raw = request.query_params.get('from_date')
        to_date_raw = request.query_params.get('to_date')
        adults = int(request.query_params.get('adults', 1))
        children = int(request.query_params.get('children', 0))

        if not from_date_raw or not to_date_raw:
            return Response({"error": "from_date and to_date are required"}, status=400)

        from_date = parse_date(from_date_raw)
        to_date = parse_date(to_date_raw)

        if not from_date or not to_date:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=400
            )

        if to_date <= from_date:
            return Response({"error": "to_date must be greater than from_date"}, status=400)

        total_people = adults + children

        reservations = Reservation.objects.filter(
            check_in_date__lte=to_date,
            check_out_date__gte=from_date,
        )

        reserved_ids = reservations.values_list('rooms__id', flat=True)

        rooms = self.get_queryset().exclude(id__in=reserved_ids).exclude(is_active=False)

        available_rooms = [
            r for r in rooms
            if r.is_free(from_date, to_date)
        ]

        if not available_rooms:
            return Response({
                "people_total": total_people,
                "options": []
            })

        # 1) First try to find single rooms that can fit everyone
        single_room_options = []
        for room in available_rooms:
            if (
                room.max_adults >= adults and
                room.max_children >= children and
                (room.max_adults + room.max_children) >= total_people
            ):
                single_room_options.append(room)

        if single_room_options:
            serialized = PublicRoomSerializer(
                single_room_options,
                many=True,
                context=self.get_serializer_context(),
            ).data
            return Response({
                "people_total": total_people,
                "mode": "single_room",
                "rooms": serialized
            })

        # 2) If no single room fits everyone, return all free rooms
        serialized_all = PublicRoomSerializer(
            available_rooms,
            many=True,
            context=self.get_serializer_context(),
        ).data
        return Response({
            "people_total": total_people,
            "mode": "multiple_rooms",
            "rooms": serialized_all
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
        responses=RoomAvailabilitySerializer,
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

        if room.is_active is False:
            return Response({"error": "Room is not active"}, status=400)


        available = room.is_available(from_date, to_date, adults, children)

        return Response({
            "room_id": room.id,
            "available": available
        })


@extend_schema_view(
    update=extend_schema(tags=['Rooms'], request=RoomSerializer, responses=RoomSerializer),
    partial_update=extend_schema(tags=['Rooms'], request=RoomSerializer, responses=RoomSerializer),
    destroy=extend_schema(tags=['Rooms']),
    create=extend_schema(tags=['Rooms'], request=RoomSerializer, responses=RoomSerializer),
)
class PrivateRoomViewSet(viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.CreateModelMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminUser]

    http_method_names = ['put', 'patch', 'delete', 'post']
