from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from pension.guest.models import Guest
from pension.guest.serializers import GuestSerializer


# Create your views here.
@extend_schema_view(
    list=extend_schema(
        tags=['Guests'],
        parameters=[
            OpenApiParameter(
                name='queryString',
                type=OpenApiTypes.STR,
                required=False,
                description='Fulltext search across first name, last name, phone, and email.',
            ),
        ],
    ),
    retrieve=extend_schema(tags=['Guests']),
    update=extend_schema(tags=['Guests']),
    partial_update=extend_schema(tags=['Guests']),
    destroy=extend_schema(tags=['Guests']),
)
class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [IsAdminUser]

    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        queryset = super().get_queryset()
        query_string = (self.request.query_params.get("queryString") or "").strip()

        if query_string:
            queryset = queryset.filter(
                Q(first_name__icontains=query_string)
                | Q(last_name__icontains=query_string)
                | Q(phone__icontains=query_string)
                | Q(email__icontains=query_string)
            )

        return queryset.order_by("-id")
