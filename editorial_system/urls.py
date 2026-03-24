from django.urls import path, include
from rest_framework import routers

from editorial_system.page.views import PageViewSet

router = routers.DefaultRouter()
router.register(r'pages', PageViewSet, basename='pages')


urlpatterns = [
    path('', include(router.urls)),
]