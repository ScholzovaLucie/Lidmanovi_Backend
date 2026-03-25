from django.contrib import admin

from pension.guest.models import Guest
from pension.reservation.models import Reservation
from pension.room.models import Room

admin.site.register(Guest)
admin.site.register(Reservation)
admin.site.register(Room)
