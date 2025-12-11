from django.urls import path, include
from rest_framework import routers

from editorial_system.iframe_embed.views import IframeEmbedViewSet
from editorial_system.info_box.views import InfoBoxViewSet
from editorial_system.media_file.views import MediaFileViewSet
from editorial_system.page.views import PageViewSet

router = routers.DefaultRouter()
router.register(r'iframes', IframeEmbedViewSet, basename='rooms')
router.register(r'info_boxes', InfoBoxViewSet, basename='info_boxes')
router.register(r'media_files', MediaFileViewSet, basename='media_files')
router.register(r'pages', PageViewSet, basename='pages')


urlpatterns = [
    path('', include(router.urls)),
]