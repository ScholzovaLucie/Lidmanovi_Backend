from drf_spectacular.types import OpenApiTypes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import viewsets, status, mixins
from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from django.utils.translation import gettext_lazy as _

from user.serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer
)

token_generator = PasswordResetTokenGenerator()


@extend_schema_view(
    retrieve=extend_schema(tags=["Users"]),
)
class UserViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # ---------------------------------------------------
    # 1) CHANGE PASSWORD
    # ---------------------------------------------------
    @extend_schema(
        tags=["Users"],
        summary=_("Change password for authenticated user"),
        description=_(
            "Requires the user to provide the current password and a new password. "
            "The old password must match. After a successful change, the password is updated."
        ),
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiTypes.STR,
            400: OpenApiTypes.STR,
        }
    )
    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_pass = serializer.validated_data["new_password"]
        user.set_password(new_pass)
        user.save()

        return Response({"detail": "Password successfully changed."})

    # ---------------------------------------------------
    # 2) PASSWORD RESET REQUEST (send email)
    # ---------------------------------------------------
    @extend_schema(
        tags=["Users"],
        summary=_("Request password reset"),
        description=_(
            "Sends a reset link to the provided email address if the user exists. "
            "The response is the same regardless of user existence for security reasons."
        ),
        request=PasswordResetRequestSerializer,
        responses={
            200: OpenApiTypes.STR,
        }
    )
    @action(detail=False, methods=["post"], url_path="password-reset-request")
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If this email exists, a reset link was sent."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        reset_link = f"{request.build_absolute_uri('/')}reset-password/?uid={uid}&token={token}"

        send_mail(
            subject="Password reset request",
            message=f"Use this link to reset your password: {reset_link}",
            from_email=None,
            recipient_list=[email],
        )

        return Response({"detail": "If this email exists, a reset link was sent."})

    # ---------------------------------------------------
    # 3) PASSWORD RESET (with token)
    # ---------------------------------------------------
    @extend_schema(
        tags=["Users"],
        summary=_("Reset password using the reset token"),
        description=_(
            "Resets the user's password using a valid token from the reset email. "
            "Requires both UID and token. If validation passes, a new password is set."
        ),
        request=PasswordResetSerializer,
        responses={
            200: OpenApiTypes.STR,
            400: OpenApiTypes.STR,
        }
    )
    @action(detail=False, methods=["post"], url_path="password-reset")
    def password_reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        uid = request.data.get("uid")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"detail": "Invalid reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password has been reset successfully."})


