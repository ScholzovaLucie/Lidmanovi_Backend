import hashlib
import json

from django.http import HttpResponseNotModified
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import serializers
from rest_framework.response import Response

from editorial_system.page.models import Page, PageTranslation
from editorial_system.page.serializers import PageSerializer, PageTranslationSerializer
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


class PageTranslationUpdateSerializer(serializers.Serializer):
    lang = serializers.CharField(help_text="Language code to override, for example en.")
    content_json = serializers.JSONField(help_text="Translated page content payload.")


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
                description="Requested response language (for example: cs, en, de). Does not filter pages, only resolves translation.",
            ),
            OpenApiParameter(
                name="source_lang",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by source language record.",
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Pages"]),
    create=extend_schema(tags=["Pages"], request=PageSerializer, responses=PageSerializer),
    update=extend_schema(tags=["Pages"], request=PageSerializer, responses=PageSerializer),
    partial_update=extend_schema(tags=["Pages"], request=PageSerializer, responses=PageSerializer),
    destroy=extend_schema(tags=["Pages"]),
)
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.prefetch_related("translations").all()
    serializer_class = PageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "translations"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        path = self.request.query_params.get("path", "").strip()
        source_lang = self.request.query_params.get("source_lang", "").strip().lower()

        if path:
            queryset = queryset.filter(path=path)
        if source_lang:
            queryset = queryset.filter(lang=source_lang)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.user.is_authenticated:
            return response

        # Public page content changes rarely. Let browsers reuse it, while the
        # content-derived ETag makes edits visible as soon as it is revalidated.
        serialized = json.dumps(response.data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        etag = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if request.headers.get("If-None-Match", "").strip('"') == etag:
            not_modified = HttpResponseNotModified()
            not_modified["ETag"] = f'"{etag}"'
            not_modified["Cache-Control"] = "public, max-age=300, must-revalidate"
            not_modified["Vary"] = "Accept-Language"
            return not_modified

        response["ETag"] = f'"{etag}"'
        response["Cache-Control"] = "public, max-age=300, must-revalidate"
        response["Vary"] = "Accept-Language"
        return response

    @extend_schema(
        tags=["Pages"],
        request=PageSerializer,
        responses={
            200: PageSerializer,
            201: PageSerializer,
        },
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

    @extend_schema(
        tags=["Pages"],
        methods=["get"],
        responses=PageTranslationSerializer(many=True),
        description="List all translations for a page.",
    )
    @extend_schema(
        tags=["Pages"],
        methods=["patch"],
        request=PageTranslationUpdateSerializer,
        responses=PageSerializer,
        description="Manually override translation for one language. Marks it as manually_reviewed.",
    )
    @action(detail=True, methods=["get", "patch"], url_path="translations")
    def translations(self, request, pk=None):
        page = self.get_object()

        if request.method == "GET":
            serializer = PageTranslationSerializer(page.translations.all(), many=True)
            return Response(serializer.data)

        target_lang = (request.data.get("lang") or "").strip().lower()
        content_json = request.data.get("content_json")

        if not target_lang:
            return Response(
                {"lang": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if content_json is None:
            return Response(
                {"content_json": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        PageTranslation.objects.update_or_create(
            page=page,
            lang=target_lang,
            defaults={"content_json": content_json, "state": TRANSLATION_MANUALLY_REVIEWED},
        )

        page.refresh_from_db()
        serializer = self.get_serializer(page)
        return Response(serializer.data, status=status.HTTP_200_OK)
