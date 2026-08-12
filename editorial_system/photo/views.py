import json
import logging
from concurrent.futures import ThreadPoolExecutor

import cloudinary.exceptions
from django.core.exceptions import TooManyFilesSent

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import decorators, mixins, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from editorial_system.photo.models import Photo, PhotoPlacement
from editorial_system.photo.serializers import (
    PhotoIdsRequestSerializer,
    PhotoPlacementSerializer,
    PhotoPlacementWriteSerializer,
    PhotoSerializer,
    PhotoUpdateSerializer,
    PhotoUploadSerializer,
)

LOGGER = logging.getLogger(__name__)

# Uploading images to Cloudinary one at a time would multiply request time by the
# batch size; a small thread pool overlaps those network waits instead.
MAX_UPLOAD_WORKERS = 6


@extend_schema_view(
    list=extend_schema(tags=["Photos"], responses=PhotoSerializer(many=True)),
    create=extend_schema(tags=["Photos"], request=PhotoUploadSerializer),
    partial_update=extend_schema(tags=["Photos"], request=PhotoUpdateSerializer),
    destroy=extend_schema(tags=["Photos"]),
)
class PhotoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Photo.objects.all()
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_permissions(self):
        if self.action in ["list", "by_ids", "by_category"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return PhotoUploadSerializer
        if self.action == "partial_update":
            return PhotoUpdateSerializer
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

            alt_text_i18n = request.data.get("alt_text_i18n", {})
            if isinstance(alt_text_i18n, str) and alt_text_i18n:
                try:
                    alt_text_i18n = json.loads(alt_text_i18n)
                except ValueError:
                    return Response(
                        {"alt_text_i18n": ["Must be a valid JSON object."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            serializers = []
            for image in images:
                serializer = self.get_serializer(
                    data={
                        "category": category,
                        "image": image,
                        "alt_text_i18n": alt_text_i18n,
                    }
                )
                serializer.is_valid(raise_exception=True)
                serializers.append(serializer)

            try:
                with ThreadPoolExecutor(max_workers=min(len(serializers), MAX_UPLOAD_WORKERS)) as executor:
                    created_photos = list(executor.map(lambda s: s.save(), serializers))
            except cloudinary.exceptions.Error as exc:
                LOGGER.error("Cloudinary upload failed: %s", exc)
                return Response(
                    {"image": ["Image upload failed. Please try again."]},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            response_serializer = PhotoSerializer(
                created_photos,
                many=True,
                context=self.get_serializer_context(),
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            photo = serializer.save()
        except cloudinary.exceptions.Error as exc:
            LOGGER.error("Cloudinary upload failed: %s", exc)
            return Response(
                {"image": ["Image upload failed. Please try again."]},
                status=status.HTTP_502_BAD_GATEWAY,
            )
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
        return [IsAdminUser()]

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