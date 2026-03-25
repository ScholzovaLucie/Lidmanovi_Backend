from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import decorators, mixins, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from editorial_system.photo.models import Photo
from editorial_system.photo.serializers import PhotoIdsRequestSerializer, PhotoSerializer, PhotoUploadSerializer


@extend_schema_view(
    list=extend_schema(tags=["Photos"], responses=PhotoSerializer(many=True)),
    create=extend_schema(tags=["Photos"], request=PhotoUploadSerializer),
)
class PhotoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Photo.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post"]

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
        images = request.FILES.getlist("images")

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
