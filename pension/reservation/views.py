from random import choices

from drf_spectacular.plumbing import build_basic_type
from rest_framework import viewsets, decorators
from rest_framework.response import Response

from pension.reservation.models import Reservation, ReservationStatus

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from pension.reservation.serializers import ReservationCreateSerializer, ReservationUpdateSerializer, ReservationReadSerializer


@extend_schema_view(
    list=extend_schema(tags=['Reservations']),
    retrieve=extend_schema(tags=['Reservations']),
    create=extend_schema(tags=['Reservations']),
    update=extend_schema(tags=['Reservations']),
    partial_update=extend_schema(tags=['Reservations']),
    destroy=extend_schema(tags=['Reservations'])
)
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()

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
        reservations = Reservation.objects.filter(check_in_date__gte=from_date, check_in_date__lte=to_date)

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

