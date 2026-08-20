from django.urls import path, include
from rest_framework import routers

from pension.amenity.views import AmenityIconViewSet
from pension.guest.views import GuestViewSet
from pension.nearby_place.views import AdminNearbyPlaceViewSet, PublicNearbyPlaceViewSet
from pension.place_rating.views import PlaceRatingView
from pension.reservation.views import PublicReservationViewSet, PrivateReservationViewSet
from pension.room.views import PublicRoomViewSet, PrivateRoomViewSet
from pension.voucher.views import PublicVoucherViewSet

router = routers.DefaultRouter()
router.register(r'public/rooms', PublicRoomViewSet, basename='public-rooms')
router.register(r'admin/rooms', PrivateRoomViewSet, basename='admin-rooms')
router.register(r'admin/guests', GuestViewSet, basename='guests')
router.register(r'admin/amenity-icons', AmenityIconViewSet, basename='amenity-icons')
router.register(r'public/reservations', PublicReservationViewSet, basename='public-reservations')
router.register(r'admin/reservations', PrivateReservationViewSet, basename='admin-reservations')
router.register(r'public/vouchers', PublicVoucherViewSet, basename='public-vouchers')
router.register(r'public/nearby-places', PublicNearbyPlaceViewSet, basename='public-nearby-places')
router.register(r'admin/nearby-places', AdminNearbyPlaceViewSet, basename='admin-nearby-places')

urlpatterns = [
    path('', include(router.urls)),
    path('public/place-rating/', PlaceRatingView.as_view(), name='place-rating'),
]
