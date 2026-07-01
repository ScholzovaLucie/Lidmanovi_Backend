from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from pension.place_rating.services import fetch_place_rating


class PlaceRatingView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ["get"]

    @extend_schema(
        tags=["Place Rating"],
        description="Return Google Maps rating and review count for the pension.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "rating": {"type": "number", "example": 4.8},
                    "review_count": {"type": "integer", "example": 758},
                },
            }
        },
    )
    def get(self, request):
        data = fetch_place_rating()
        return Response(data)
