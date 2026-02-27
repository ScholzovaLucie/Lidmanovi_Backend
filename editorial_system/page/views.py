from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from editorial_system.page.models import Page
from editorial_system.page.serializers import PageSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Pages"],
        parameters=[
            OpenApiParameter(
                name="path",
                type=OpenApiTypes.STR,
                required=False,
                description="Exact route path filter (for example: /kontakt).",
            ),
            OpenApiParameter(
                name="lang",
                type=OpenApiTypes.STR,
                required=False,
                description="Language filter (for example: cs, en, de).",
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Pages"]),
    create=extend_schema(tags=["Pages"]),
    update=extend_schema(tags=["Pages"]),
    partial_update=extend_schema(tags=["Pages"]),
    destroy=extend_schema(tags=["Pages"]),
)
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        path = self.request.query_params.get("path")
        lang = self.request.query_params.get("lang")

        if path is not None:
            queryset = queryset.filter(path=path.strip())
        if lang is not None:
            queryset = queryset.filter(lang=lang.strip().lower())

        return queryset

    @extend_schema(
        tags=["Pages"],
        parameters=[
            OpenApiParameter(
                name="path",
                type=OpenApiTypes.STR,
                required=False,
                description="Path can be provided in body or query param.",
            ),
            OpenApiParameter(
                name="lang",
                type=OpenApiTypes.STR,
                required=False,
                description="Lang can be provided in body or query param.",
            ),
        ],
        description="Upsert page by path+lang. Updates existing page or creates a new one.",
    )
    @action(detail=False, methods=["put", "patch"], url_path="upsert")
    def upsert(self, request):
        payload = request.data.copy()
        path = payload.get("path") or request.query_params.get("path")
        lang = payload.get("lang") or request.query_params.get("lang")

        if not path or not str(path).strip():
            return Response(
                {"path": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not lang or not str(lang).strip():
            return Response(
                {"lang": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_path = str(path).strip()
        if not normalized_path.startswith("/"):
            normalized_path = f"/{normalized_path}"
        normalized_lang = str(lang).strip().lower()
        payload["path"] = normalized_path
        payload["lang"] = normalized_lang

        page = Page.objects.filter(path=normalized_path, lang=normalized_lang).first()
        partial = request.method.lower() == "patch"

        if page:
            serializer = self.get_serializer(page, data=payload, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=payload, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
