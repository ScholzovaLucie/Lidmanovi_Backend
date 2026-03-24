from django.urls import path, include
from rest_framework import routers

from editorial_system.page.views import PageViewSet
from editorial_system.info_box.views import InfoBoxViewSet

router = routers.DefaultRouter()
router.register(r'pages', PageViewSet, basename='pages')
router.register(r'info-boxes', InfoBoxViewSet, basename='info-boxes')


urlpatterns = [
    path('', include(router.urls)),
]