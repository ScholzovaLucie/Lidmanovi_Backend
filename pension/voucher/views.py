from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, decorators
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from emails.services import send_templated_email
from pension.voucher.models import VoucherAmount, VoucherOrder
from pension.voucher.serializers import (
    VoucherAmountSerializer,
    VoucherOrderCreateSerializer,
    VoucherOrderReadSerializer,
)


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
        amounts = VoucherAmount.objects.filter(is_active=True)
        return Response(VoucherAmountSerializer(amounts, many=True).data)

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
            context={
                "name": f"{voucher_order.guest.first_name} {voucher_order.guest.last_name}",
                "number": voucher_order.number,
                "amount": voucher_order.amount,
                "currency": voucher_order.currency,
            },
        )

        read_serializer = VoucherOrderReadSerializer(voucher_order)
        return Response(read_serializer.data)
