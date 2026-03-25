from django.contrib import admin

from editorial_system.page.models import Page
from editorial_system.info_box.models import InfoBox
from editorial_system.photo.models import Photo

admin.site.register(Page)
admin.site.register(InfoBox)
admin.site.register(Photo)

