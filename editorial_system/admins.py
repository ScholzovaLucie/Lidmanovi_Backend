from django.contrib import admin

from editorial_system.iframe_embed.models import IframeEmbed
from editorial_system.info_box.models import InfoBox
from editorial_system.media_file.models import MediaFile
from editorial_system.page.models import Page

admin.site.register(IframeEmbed)
admin.site.register(InfoBox)
admin.site.register(MediaFile)
admin.site.register(Page)


