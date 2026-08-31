import logging

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, decorators, mixins
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from emails.services import send_templated_email
from pension.voucher.enums import VoucherStatus
from pension.voucher.models import STATUS_MAP_TO_MAIL, VoucherAmount, VoucherOrder
from pension.voucher.serializers import (
    AdminVoucherAmountSerializer,
    VoucherAmountSerializer,
    VoucherOrderCreateSerializer,
    VoucherOrderReadSerializer,
    VoucherOrderStatusSerializer,
    VoucherOrderUpdateSerializer,
)

LOGGER_EMAIL = logging.getLogger("emails")


def _voucher_email_context(voucher_order):
    return {
        "name": f"{voucher_order.guest.first_name} {voucher_order.guest.last_name}",
        "guest_email": voucher_order.guest.email,
        "number": voucher_order.number,
        "amount": voucher_order.amount,
        "currency": voucher_order.currency,
        "delivery_method": voucher_order.get_delivery_method_display(),
        "shipping_address": voucher_order.full_shipping_address,
    }


class PublicVoucherViewSet(viewsets.GenericViewSet):
    queryset = VoucherOrder.objects.select_related('guest')
    permission_classes = []

    def get_throttles(self):
        if self.action == 'create_voucher_order':
            self.throttle_scope = 'voucher_create'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == 'create_voucher_order':
            return VoucherOrderCreateSerializer
        return VoucherOrderReadSerializer

    @extend_schema(
        tags=['Vouchers'],
        responses=VoucherAmountSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='amounts')
    def get_amounts(self, request):
        amounts = VoucherAmount.objects.filter(is_active=True, deleted_at__isnull=True)
        return Response(VoucherAmountSerializer(amounts, many=True).data)

    @extend_schema(
        tags=['Vouchers'],
        responses=VoucherOrderStatusSerializer(many=True),
    )
    @decorators.action(detail=False, methods=['get'], url_path='statuses')
    def get_statuses(self, request):
        data = [
            {
                "value": choice[0],
                "label": choice[1],
            }
            for choice in VoucherStatus.choices
        ]
        return Response(data)

    @extend_schema(
        tags=['Vouchers'],
        request=VoucherOrderCreateSerializer,
        responses=VoucherOrderReadSerializer,
    )
    @decorators.action(detail=False, methods=['post'], url_path='create')
    def create_voucher_order(self, request):
        serializer = VoucherOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voucher_order = serializer.save()

        send_templated_email(
            email_type="voucher_order_received",
            recipient=voucher_order.guest.email,
            context=_voucher_email_context(voucher_order),
        )

        if settings.ADMIN_NOTIFICATION_EMAIL:
            send_templated_email(
                email_type="admin_new_voucher_order",
                recipient=settings.ADMIN_NOTIFICATION_EMAIL,
                context=_voucher_email_context(voucher_order),
            )

        read_serializer = VoucherOrderReadSerializer(voucher_order)
        return Response(read_serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Vouchers']),
    retrieve=extend_schema(tags=['Vouchers']),
    create=extend_schema(tags=['Vouchers']),
    update=extend_schema(tags=['Vouchers']),
    destroy=extend_schema(tags=['Vouchers']),
)
class AdminVoucherAmountViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = VoucherAmount.objects.filter(deleted_at__isnull=True)
    serializer_class = AdminVoucherAmountSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    http_method_names = ['get', 'post', 'put', 'delete']

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])


@extend_schema_view(
    list=extend_schema(
        tags=['Vouchers'],
        parameters=[
            OpenApiParameter(
                name='status',
                required=False,
                description='Voucher order status',
                type=OpenApiTypes.STR,
                enum=[choice[0] for choice in VoucherStatus.choices],
            ),
            OpenApiParameter(
                name='delivery_method',
                required=False,
                description='Delivery method',
                type=OpenApiTypes.STR,
                enum=[choice[0] for choice in VoucherOrder.DeliveryMethod.choices],
            ),
            OpenApiParameter(
                name='guest_email',
                required=False,
                description='Guest email',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='guest_last_name',
                required=False,
                description='Guest last name',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='search_text',
                required=False,
                description='Generic text search across voucher order and guest string fields.',
                type=OpenApiTypes.STR,
            ),
        ],
    ),
    retrieve=extend_schema(tags=['Vouchers']),
)
class PrivateVoucherViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = VoucherOrder.objects.select_related('guest')
    permission_classes = [IsAdminUser]

    @staticmethod
    def _apply_default_ordering(queryset):
        return queryset.order_by('-created_at', '-id')

    def get_serializer_class(self):
        if self.action in ('update_voucher_order',):
            return VoucherOrderUpdateSerializer
        return VoucherOrderReadSerializer

    def get_queryset(self):
        queryset = VoucherOrder.objects.select_related('guest')

        status = self.request.query_params.get('status')
        delivery_method = self.request.query_params.get('delivery_method')
        guest_email = self.request.query_params.get('guest_email')
        guest_last_name = self.request.query_params.get('guest_last_name')
        search_text = (self.request.query_params.get('search_text') or '').strip()

        if status:
            queryset = queryset.filter(status=status)

        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)

        if guest_email:
            queryset = queryset.filter(guest__email__iexact=guest_email)

        if guest_last_name:
            queryset = queryset.filter(guest__last_name__icontains=guest_last_name)

        if search_text:
            queryset = queryset.filter(
                Q(number__icontains=search_text)
                | Q(status__icontains=search_text)
                | Q(note__icontains=search_text)
                | Q(currency__icontains=search_text)
                | Q(guest__first_name__icontains=search_text)
                | Q(guest__last_name__icontains=search_text)
                | Q(guest__email__icontains=search_text)
                | Q(guest__phone__icontains=search_text)
            )

        return self._apply_default_ordering(queryset.distinct())

    @extend_schema(
        tags=['Vouchers'],
        request=VoucherOrderUpdateSerializer,
        responses=VoucherOrderReadSerializer,
    )
    @decorators.action(detail=True, methods=['put'], url_path='update')
    def update_voucher_order(self, request, pk=None):
        voucher_order = self.get_object()

        serializer = VoucherOrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'status' in data and data['status'] is not None:
            status = data['status']
            voucher_order.status = status

            update_fields = ["status"]
            if status == VoucherStatus.SENT and voucher_order.sent_at is None:
                voucher_order.sent_at = timezone.now()
                update_fields.append("sent_at")

            voucher_order.save(update_fields=update_fields)

            template_name = STATUS_MAP_TO_MAIL.get(status)
            if not template_name:
                LOGGER_EMAIL.warning(f"Unknown status {status} email not sent")
            else:
                send_templated_email(
                    email_type=template_name,
                    recipient=voucher_order.guest.email,
                    context=_voucher_email_context(voucher_order),
                )
                LOGGER_EMAIL.info(f"Email {template_name} sent to {voucher_order.guest.email}")

        read_serializer = VoucherOrderReadSerializer(voucher_order)
        return Response(read_serializer.data)
