from django.shortcuts import render
from rest_framework import viewsets

from pension.reservation.models import Reservation

from drf_spectacular.utils import extend_schema_view, extend_schema

from pension.reservation.serializers import ReservationSerializer


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
    serializer_class = ReservationSerializer