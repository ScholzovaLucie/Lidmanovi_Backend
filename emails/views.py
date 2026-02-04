from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SendEmailSerializer, SendEmailResponseSerializer, ErrorResponseSerializer
from .services import send_templated_email

class SendEmailView(GenericAPIView):
    serializer_class = SendEmailSerializer

    @extend_schema(
        request=SendEmailSerializer,
        responses={
            200: SendEmailResponseSerializer,
            400: ErrorResponseSerializer,
        },
        description="Send templated email based on type."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            send_templated_email(
                email_type=data["type"],
                recipient=data["recipient"],
                context={
                    "name": data.get("customer_name"),
                    "date_from": data.get("date_from"),
                    "date_to": data.get("date_to"),
                    "persons": data.get("persons"),
                    "reason": data.get("reason"),
                    "message": data.get("message"),
                },
            )

            return Response({"status": "sent"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)