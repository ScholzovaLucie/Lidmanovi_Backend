from django.shortcuts import render
from rest_framework import viewsets
from pension.reservation_item.models import ReservationItem
from drf_spectacular.utils import extend_schema_view, extend_schema

from pension.reservation_item.serializers import ReservationItemSerializer


@extend_schema_view(
    list=extend_schema(tags=['Reservation items']),
    retrieve=extend_schema(tags=['Reservation items']),
    create=extend_schema(tags=['Reservation items']),
    update=extend_schema(tags=['Reservation items']),
    partial_update=extend_schema(tags=['Reservation items']),
    destroy=extend_schema(tags=['Reservation items']),
)
class ReservationItemViewSet(viewsets.ModelViewSet):
    queryset = ReservationItem.objects.all()
    serializer_class = ReservationItemSerializer
