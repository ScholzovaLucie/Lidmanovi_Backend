import logging
from io import BytesIO

from django.db.models import Q
from drf_spectacular.plumbing import build_basic_type
from rest_framework import viewsets, decorators, mixins, serializers, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from emails.services import send_templated_email
from pension.reservation.bulk_import import BulkImportError, import_reservations
from pension.reservation.models import Reservation, ReservationStatus, STATUS_MAP_TO_MAIL

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from pension.reservation.serializers import (
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationReadSerializer, ReservationCancelSerializer, ReservationStatusSerializer,
)

LOGGER_EMAIL = logging.getLogger("emails")


def _get_room_names(reservation):
    return ", ".join(reservation.rooms.values_list('name', flat=True))


@extend_schema_view(
)
class PublicReservationViewSet(viewsets.GenericViewSet):
    queryset = Reservation.objects.select_related('primary_guest').prefetch_related('rooms')
    permission_classes = []

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationReadSerializer

    @extend_schema(
        tags=['Reservations'],
        request=ReservationCreateSerializer,
        responses=ReservationReadSerializer(many=False),
    )
    @decorators.action(detail=False, methods=['post'], url_path='create')
    def create_reservation(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = serializer.save()

        read_serializer = ReservationReadSerializer(reservation)
        data = read_serializer.data
        instance = read_serializer.instance

        room_names = ", ".join(r['name'] for r in data['rooms'])

        send_templated_email(
            email_type="reservation_received",
            recipient=instance.primary_guest.email,
            context={
                "name": f"{instance.primary_guest.first_name} {instance.primary_guest.last_name}",
                "date_from": instance.check_in_date,
                "date_to": instance.check_out_date,
                "adults": instance.num_adults,
                "children": instance.num_children,
                "price": instance.price,
                "room_type": room_names,
            },
        )

        return Response(data)

    @extend_schema(
        tags=['Reservations'],
        responses=ReservationStatusSerializer(many=True),
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
    list=extend_schema(
        tags=['Reservations'],
        parameters=[
            OpenApiParameter(
                name='reservation_from',
                type=OpenApiTypes.DATE,
                required=False,
                description='Reservation period start (YYYY-MM-DD). Works with reservation_to as overlap filter.',
            ),
            OpenApiParameter(
                name='reservation_to',
                type=OpenApiTypes.DATE,
                required=False,
                description='Reservation period end (YYYY-MM-DD). Works with reservation_from as overlap filter.',
            ),
            OpenApiParameter(
                name='status',
                required=False,
                description='Reservation status',
                type=OpenApiTypes.STR,
                enum=[choice[0] for choice in ReservationStatus.choices],
            ),
            OpenApiParameter(
                name='room_id',
                required=False,
                description='Room ID',
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name='primary_guest_email',
                required=False,
                description='Primary guest email',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='primary_guest_last_name',
                required=False,
                description='Primary guest last name',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='primary_guest_id',
                required=False,
                description='Primary guest ID',
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name='search_text',
                required=False,
                description='Generic text search across reservation, guest, and room string fields.',
                type=OpenApiTypes.STR,
            ),
        ],
    ),
    retrieve=extend_schema(tags=['Reservations']),
)
class PrivateReservationViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Reservation.objects.select_related('primary_guest').prefetch_related('rooms')
    permission_classes = [IsAdminUser]

    @staticmethod
    def _apply_default_ordering(queryset):
        return queryset.order_by('-created_at', '-id')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        if self.action in ('update', 'partial_update'):
            return ReservationUpdateSerializer
        return ReservationReadSerializer

    def _parse_date_param(self, name):
        value = self.request.query_params.get(name)
        if not value:
            return None

        field = serializers.DateField()
        try:
            return field.to_internal_value(value)
        except serializers.ValidationError:
            raise serializers.ValidationError({name: "Invalid date format. Use YYYY-MM-DD."})

    def get_queryset(self):
        queryset = Reservation.objects.select_related('primary_guest').prefetch_related('rooms')

        reservation_from = self._parse_date_param('reservation_from')
        reservation_to = self._parse_date_param('reservation_to')
        status = self.request.query_params.get('status')
        room_id = self.request.query_params.get('room_id')
        primary_guest_email = self.request.query_params.get('primary_guest_email')
        primary_guest_last_name = self.request.query_params.get('primary_guest_last_name')
        primary_guest_id = self.request.query_params.get('primary_guest_id')
        search_text = (self.request.query_params.get('search_text') or '').strip()

        if reservation_from:
            queryset = queryset.filter(check_out_date__gte=reservation_from)

        if reservation_to:
            queryset = queryset.filter(check_in_date__lte=reservation_to)

        if status:
            queryset = queryset.filter(status=status)

        if room_id:
            queryset = queryset.filter(rooms__id=room_id)

        if primary_guest_email:
            queryset = queryset.filter(primary_guest__email__iexact=primary_guest_email)

        if primary_guest_last_name:
            queryset = queryset.filter(primary_guest__last_name__icontains=primary_guest_last_name)

        if primary_guest_id:
            queryset = queryset.filter(primary_guest_id=primary_guest_id)

        if search_text:
            queryset = queryset.filter(
                Q(number__icontains=search_text)
                | Q(status__icontains=search_text)
                | Q(note__icontains=search_text)
                | Q(currency__icontains=search_text)
                | Q(primary_guest__first_name__icontains=search_text)
                | Q(primary_guest__last_name__icontains=search_text)
                | Q(primary_guest__email__icontains=search_text)
                | Q(primary_guest__phone__icontains=search_text)
                | Q(primary_guest__country__icontains=search_text)
                | Q(primary_guest__note__icontains=search_text)
                | Q(rooms__name__icontains=search_text)
                | Q(rooms__description__icontains=search_text)
            )

        return self._apply_default_ordering(queryset.distinct())

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
        from_date = self._parse_date_param('from_date')
        to_date = self._parse_date_param('to_date')
        reservations = self._apply_default_ordering(
            Reservation.objects.select_related('primary_guest').prefetch_related('rooms').filter(
                check_in_date__lte=to_date,
                check_out_date__gte=from_date,
            )
        )
        page = self.paginate_queryset(reservations)
        if page is not None:
            serializer = ReservationReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

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

        reservations = self._apply_default_ordering(
            Reservation.objects.select_related('primary_guest').prefetch_related('rooms').filter(status=status)
        )

        page = self.paginate_queryset(reservations)
        if page is not None:
            serializer = ReservationReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

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
            status = data['status']
            reservation.status = status
            reservation.save(update_fields=["status"])

            template_name = STATUS_MAP_TO_MAIL.get(status)
            if not template_name:
                LOGGER_EMAIL.warning(f"Unknown status {status} email not sent")

            else:
                send_templated_email(
                    email_type=template_name,
                    recipient=reservation.primary_guest.email,
                    context={
                        "name": f"{reservation.primary_guest.first_name} {reservation.primary_guest.last_name}",
                        "date_from": reservation.check_in_date,
                        "date_to": reservation.check_out_date,
                        "adults": reservation.num_adults,
                        "children": reservation.num_children,
                        "price": reservation.price,
                        "room_type": _get_room_names(reservation),
                    },
                )
                LOGGER_EMAIL.info(f"Email {template_name} sent to {reservation.primary_guest.email}")

        read_serializer = ReservationReadSerializer(reservation)

        return Response(read_serializer.data)

    @extend_schema(
        tags=['Reservations'],
        request=ReservationCancelSerializer,
        responses=ReservationReadSerializer,
    )
    @decorators.action(detail=True, methods=['post'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        reservation = self.get_object()

        serializer = ReservationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cancel_reason = data['cancel_reason']

        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"])

        send_templated_email(
            email_type="reservation_rejected",
            recipient=reservation.primary_guest.email,
            context={
                "name": f"{reservation.primary_guest.first_name} {reservation.primary_guest.last_name}",
                "date_from": reservation.check_in_date,
                "date_to": reservation.check_out_date,
                "adults": reservation.num_adults,
                "children": reservation.num_children,
                "price": reservation.price,
                "room_type": _get_room_names(reservation),
                "reason": cancel_reason
            },
        )

        return Response(ReservationReadSerializer(reservation).data)

    @extend_schema(
        tags=['Reservations'],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary', 'description': 'The .xlsx file to import.'},
                    'sheet': {'type': 'string', 'description': 'Sheet name to read (default: active sheet).'},
                    'dry_run': {'type': 'boolean', 'description': 'Validate only, write nothing to the database.'},
                },
                'required': ['file'],
            }
        },
        responses={
            200: build_basic_type(OpenApiTypes.OBJECT),
            400: build_basic_type(OpenApiTypes.OBJECT),
        },
    )
    @decorators.action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        uploaded_file = request.FILES.get('file')
        if uploaded_file is None:
            return Response({"file": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        dry_run = str(request.data.get('dry_run', 'false')).strip().lower() in ('1', 'true', 'yes', 'on')
        sheet_name = request.data.get('sheet') or None

        try:
            import openpyxl
        except ImportError:
            return Response(
                {"file": ["Server is missing the openpyxl dependency."]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            workbook = openpyxl.load_workbook(BytesIO(uploaded_file.read()), data_only=True)
        except Exception as exc:
            return Response(
                {"file": [f"Could not read the uploaded file: {exc}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = import_reservations(workbook, sheet_name=sheet_name, dry_run=dry_run)
        except BulkImportError as exc:
            return Response({"file": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)
