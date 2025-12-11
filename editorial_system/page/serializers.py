from rest_framework import serializers

from editorial_system.page.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'