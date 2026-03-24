from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from editorial_system.page.models import Page
from editorial_system.page.serializers import PageSerializer
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


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
                description="Requested response language (for example: cs, en, de).",
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
        path = self.request.query_params.get("path", "").strip()
        lang = self.request.query_params.get("lang", "").strip().lower()
        source_lang = self.request.query_params.get("source_lang", "").strip().lower()

        if path:
            queryset = queryset.filter(path=path)
        if source_lang:
            queryset = queryset.filter(lang=source_lang)
            return queryset

        if lang and path:
            exact_match = queryset.filter(lang=lang)
            if exact_match.exists():
                return exact_match

            source_fallback = queryset.filter(lang="cs")
            if source_fallback.exists():
                return source_fallback

            return queryset.order_by("id")[:1]

        if lang and not path:
            queryset = queryset.filter(lang=lang)

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

    @extend_schema(
        tags=["Pages"],
        description="Manually override translation for one language.",
    )
    @action(detail=True, methods=["patch"], url_path="translations")
    def translations(self, request, pk=None):
        page = self.get_object()
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

        content_i18n = dict(page.content_i18n or {})
        translation_state_i18n = dict(page.translation_state_i18n or {})

        content_i18n[target_lang] = content_json
        translation_state_i18n[target_lang] = {
            "state": TRANSLATION_MANUALLY_REVIEWED,
        }

        page.content_i18n = content_i18n
        page.translation_state_i18n = translation_state_i18n
        page.save(update_fields=["content_i18n", "translation_state_i18n"])

        serializer = self.get_serializer(page)
        return Response(serializer.data, status=status.HTTP_200_OK)
