from django.contrib import admin

from pension.guest.models import Guest
from pension.package.models import Package
from pension.reservation.models import Reservation
from pension.reservation_item.models import ReservationItem
from pension.room.models import Room

admin.site.register(Guest)
admin.site.register(Reservation)
admin.site.register(ReservationItem)
admin.site.register(Room)
admin.site.register(Package)

