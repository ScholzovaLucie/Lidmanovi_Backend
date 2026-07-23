from django.core.exceptions import TooManyFilesSent

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import decorators, mixins, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from editorial_system.photo.models import Photo, PhotoPlacement
from editorial_system.photo.serializers import (
    PhotoIdsRequestSerializer,
    PhotoPlacementSerializer,
    PhotoPlacementWriteSerializer,
    PhotoSerializer,
    PhotoUploadSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Photos"], responses=PhotoSerializer(many=True)),
    create=extend_schema(tags=["Photos"], request=PhotoUploadSerializer),
    destroy=extend_schema(tags=["Photos"]),
)
class PhotoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Photo.objects.all()
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "delete"]

    def get_permissions(self):
        if self.action in ["list", "by_ids", "by_category"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return PhotoUploadSerializer
        return PhotoSerializer

    @extend_schema(
        tags=["Photos"],
        request=PhotoIdsRequestSerializer,
        responses=PhotoSerializer(many=True),
    )
    @decorators.action(detail=False, methods=["post"], url_path="by-ids")
    def by_ids(self, request):
        serializer = PhotoIdsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        photos = list(Photo.objects.filter(id__in=ids))
        photos_by_id = {photo.id: photo for photo in photos}
        ordered_photos = [photos_by_id[photo_id] for photo_id in ids if photo_id in photos_by_id]

        response_serializer = PhotoSerializer(
            ordered_photos,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)

    @extend_schema(
        tags=["Photos"],
        parameters=[
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                required=True,
                description="Photo category.",
            ),
        ],
        responses=PhotoSerializer(many=True),
    )
    @decorators.action(detail=False, methods=["get"], url_path="by-category")
    def by_category(self, request):
        category = request.query_params.get("category")
        if not category:
            return Response(
                {"category": ["This query parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photos = self.get_queryset().filter(category__iexact=category)
        response_serializer = PhotoSerializer(
            photos,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            images = request.FILES.getlist("images")
        except TooManyFilesSent:
            return Response(
                {"images": ["Překročen maximální počet souborů. Nahrajte méně souborů najednou."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if images:
            category = request.data.get("category")
            if not category:
                return Response(
                    {"category": ["This field is required."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_photos = []
            for image in images:
                serializer = self.get_serializer(data={"category": category, "image": image})
                serializer.is_valid(raise_exception=True)
                created_photos.append(serializer.save())

            response_serializer = PhotoSerializer(
                created_photos,
                many=True,
                context=self.get_serializer_context(),
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        response_serializer = PhotoSerializer(photo, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        tags=["Photo Placements"],
        parameters=[
            OpenApiParameter(
                name="location",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter placements by location (e.g. 'hero', 'gallery').",
            ),
        ],
        responses=PhotoPlacementSerializer(many=True),
    ),
    create=extend_schema(tags=["Photo Placements"], request=PhotoPlacementWriteSerializer),
    partial_update=extend_schema(tags=["Photo Placements"], request=PhotoPlacementWriteSerializer),
    destroy=extend_schema(tags=["Photo Placements"]),
)
class PhotoPlacementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PhotoPlacement.objects.select_related("photo").all()
    http_method_names = ["get", "post", "patch", "delete"]

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return PhotoPlacementWriteSerializer
        return PhotoPlacementSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        location = self.request.query_params.get("location")
        if location:
            qs = qs.filter(location__iexact=location)
        return qs

    def get_serializer_context(self):
        return super().get_serializer_context()