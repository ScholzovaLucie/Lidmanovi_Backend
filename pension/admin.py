from django.contrib import admin

from pension.guest.models import Guest
from pension.reservation.models import Reservation
from pension.room.models import Room


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'country')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('country',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'max_adults', 'max_children', 'price_for_adult', 'price_for_children', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'check_in_date', 'check_out_date', 'primary_guest', 'num_adults', 'num_children', 'price')
    list_filter = ('status',)
    search_fields = ('number', 'primary_guest__first_name', 'primary_guest__last_name', 'primary_guest__email')
    date_hierarchy = 'check_in_date'
    raw_id_fields = ('primary_guest',)
