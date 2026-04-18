import smtplib

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .serializers import SendEmailSerializer, SendEmailResponseSerializer, ErrorResponseSerializer
from .services import send_templated_email


class SendEmailView(GenericAPIView):
    serializer_class = SendEmailSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=SendEmailSerializer,
        responses={
            200: SendEmailResponseSerializer,
            400: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
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
                    "name": data.get("recipient_name"),
                    "date_from": data.get("date_from"),
                    "date_to": data.get("date_to"),
                    "persons": data.get("persons"),
                    "reason": data.get("reason"),
                    "message": data.get("message"),
                },
                raise_on_error=True,
            )

            return Response({"status": "sent"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (smtplib.SMTPException, OSError) as e:
            return Response({"detail": "Email delivery failed."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
