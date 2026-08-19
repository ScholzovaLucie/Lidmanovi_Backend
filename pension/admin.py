from django.contrib import admin
from django.utils import timezone

from pension.amenity.models import AmenityIcon
from pension.guest.models import Guest
from pension.reservation.models import Reservation
from pension.room.models import Room
from pension.voucher.models import VoucherAmount, VoucherOrder


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'country')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('country',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'price_for_adult', 'price_for_children', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'check_in_date', 'check_out_date', 'primary_guest', 'num_adults', 'num_children', 'price')
    list_select_related = ('primary_guest',)
    list_filter = ('status',)
    search_fields = ('number', 'primary_guest__first_name', 'primary_guest__last_name', 'primary_guest__email')
    date_hierarchy = 'check_in_date'
    raw_id_fields = ('primary_guest',)


@admin.register(AmenityIcon)
class AmenityIconAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('key', 'label')
    ordering = ('order', 'id')


@admin.register(VoucherAmount)
class VoucherAmountAdmin(admin.ModelAdmin):
    list_display = ('value', 'currency', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    list_filter = ('currency', 'is_active')
    ordering = ('sort_order', 'value')


@admin.register(VoucherOrder)
class VoucherOrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'guest', 'amount', 'currency', 'created_at', 'is_sent', 'sent_at')
    list_editable = ('is_sent',)
    list_filter = ('is_sent', 'currency')
    search_fields = ('number', 'guest__first_name', 'guest__last_name', 'guest__email')
    date_hierarchy = 'created_at'
    raw_id_fields = ('guest',)
    readonly_fields = ('number', 'created_at', 'sent_at')

    def save_model(self, request, obj, form, change):
        if change and 'is_sent' in form.changed_data:
            obj.sent_at = timezone.now() if obj.is_sent else None
        super().save_model(request, obj, form, change)
