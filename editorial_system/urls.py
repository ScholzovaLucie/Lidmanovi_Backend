from django.urls import path, include
from rest_framework import routers

from editorial_system.page.views import PageViewSet
from editorial_system.info_box.views import InfoBoxViewSet, PublicInfoBoxViewSet
from editorial_system.photo.views import PhotoViewSet

router = routers.DefaultRouter()
router.register(r'pages', PageViewSet, basename='pages')
router.register(r'info-boxes', InfoBoxViewSet, basename='info-boxes')
router.register(r'public/info-boxes', PublicInfoBoxViewSet, basename='public-info-boxes')
router.register(r'photos', PhotoViewSet, basename='photos')


urlpatterns = [
    path('', include(router.urls)),
]
