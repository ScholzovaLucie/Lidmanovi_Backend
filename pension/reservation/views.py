from random import choices

from drf_spectacular.plumbing import build_basic_type
from rest_framework import viewsets, decorators, mixins
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from pension.reservation.models import Reservation, ReservationStatus

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from pension.reservation.serializers import (
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationReadSerializer,
)


@extend_schema_view(
)
class PublicReservationViewSet(viewsets.GenericViewSet):
    queryset = Reservation.objects.all()
    permission_classes = []

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationReadSerializer

    @extend_schema(
        tags=['Reservations'],
        request=ReservationCreateSerializer,
        responses=ReservationReadSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['post'], url_path='create')
    def create_reservation(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = serializer.save()

        read_serializer = ReservationReadSerializer(reservation)
        return Response(read_serializer.data)


    @extend_schema(
        tags=['Reservations'],
        responses=OpenApiTypes.OBJECT,
    )
    @decorators.action(detail=False, methods=['get'], url_path='statuses')
    def get_statuses(self, request):
        data = [
            {
                "value": choice[0],
                "label": choice[1],
            }
            for choice in ReservationStatus.choices
        ]
        return Response(data)


@extend_schema_view(
    list=extend_schema(tags=['Reservations']),
    retrieve=extend_schema(tags=['Reservations']),
)
class PrivateReservationViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Reservation.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        if self.action in ('update', 'partial_update'):
            return ReservationUpdateSerializer
        return ReservationReadSerializer

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
        responses=ReservationReadSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='by-date')
    def get_operation_by_date(self, request):
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        reservations = Reservation.objects.filter(
            check_in_date__lte=to_date,
            check_out_date__gte=from_date,
        )
        serializer = ReservationReadSerializer(reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Reservations'],
        parameters=[
            OpenApiParameter(
                name='status',
                required=True,
                description='Reservation status',
                type=OpenApiTypes.STR,
                enum=[choice[0] for choice in ReservationStatus.choices],

            )
        ],
        responses=ReservationReadSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='by-status')
    def get_operation_by_status(self, request):
        status = request.query_params.get('status')

        reservations = Reservation.objects.filter(status=status)

        serializer = ReservationReadSerializer(reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Reservations'],
        request=ReservationUpdateSerializer,
        responses=ReservationReadSerializer,
    )
    @decorators.action(detail=True, methods=['put'], url_path='update')
    def update_reservation(self, request, pk=None):
        reservation = self.get_object()

        serializer = ReservationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if 'status' in data and data['status'] is not None:
            reservation.status = data['status']

        reservation.save()

        read_serializer = ReservationReadSerializer(reservation)
        return Response(read_serializer.data)