from django.urls import path, include
from rest_framework import routers

from pension.guest.views import GuestViewSet
from pension.package.views import PackageViewSet
from pension.reservation.views import ReservationViewSet
from pension.reservation_item.views import ReservationItemViewSet
from pension.room.views import RoomViewSet

router = routers.DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='rooms')
router.register(r'guests', GuestViewSet, basename='guests')
router.register(r'packages', PackageViewSet, basename='packages')
router.register(r'reservations', ReservationViewSet, basename='reservations')
router.register(r'reservation_items', ReservationItemViewSet, basename='reservation_items')


urlpatterns = [
    path('', include(router.urls)),
]
