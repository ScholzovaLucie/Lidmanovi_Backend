from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from pension.app_setting.models import AppSetting
from pension.app_setting.serializers import AppSettingSerializer


class AppSettingsView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAdminUser()]

    def get(self, request):
        return Response(dict(AppSetting.objects.values_list("key", "value")))

    def post(self, request):
        serializer = AppSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        setting, _ = AppSetting.objects.update_or_create(
            key=serializer.validated_data["key"],
            defaults={"value": serializer.validated_data["value"]},
        )
        return Response({"key": setting.key, "value": setting.value})
