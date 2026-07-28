from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, Company

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID


@api_view(["POST"])
def google_login(request):

    token = request.data.get("token")

    if not token:
        return Response(
            {"error": "Token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        email = info["email"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": info.get("given_name", ""),
                "last_name": info.get("family_name", ""),
            },
        )

        user.google_id = info["sub"]
        user.email_verified = info.get("email_verified", False)
        user.save()

        Company.objects.get_or_create(
            owner=user
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "name": user.get_full_name(),
                    "email": user.email,
                },
                "redirect": "/dashboard"
            }
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_401_UNAUTHORIZED,
        )