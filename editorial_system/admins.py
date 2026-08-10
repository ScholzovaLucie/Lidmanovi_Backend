from django.contrib import admin

from editorial_system.page.models import Page
from editorial_system.info_box.models import InfoBox
from editorial_system.photo.models import Photo


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('path', 'lang')
    search_fields = ('path',)


@admin.register(InfoBox)
class InfoBoxAdmin(admin.ModelAdmin):
    list_display = ('id', 'starts_at', 'ends_at')
    search_fields = ('title_i18n',)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('category',)
