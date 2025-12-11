from rest_framework import serializers

from editorial_system.info_box.models import InfoBox


class InfoBoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfoBox
        fields = '__all__'