from django.urls import path, include
from rest_framework import routers

from pension.guest.views import GuestViewSet
from pension.reservation.views import ReservationViewSet
from pension.room.views import PublicRoomViewSet, PrivateRoomViewSet

router = routers.DefaultRouter()
router.register(r'public/rooms', PublicRoomViewSet, basename='public-rooms')
router.register(r'admin/rooms', PrivateRoomViewSet, basename='admin-rooms')
router.register(r'guests', GuestViewSet, basename='guests')
router.register(r'reservations', ReservationViewSet, basename='reservations')

urlpatterns = [
    path('', include(router.urls)),
]
