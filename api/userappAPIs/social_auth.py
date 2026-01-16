import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..database import execute_query, execute_insert
from ..auth import create_access_token

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"


class SocialLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")

        if provider not in ["google", "facebook"]:
            return Response({"error": "provider буруу байна"}, status=400)

        if not access_token:
            return Response({"error": "access_token заавал"}, status=400)

        # ===== GOOGLE =====
        if provider == "google":
            userinfo = requests.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            ).json()

            if "email" not in userinfo:
                return Response({"error": "Google token буруу"}, status=401)

            email = userinfo["email"]
            full_name = userinfo.get("name", "")
            profile_image = userinfo.get("picture")

        # ===== FACEBOOK =====
        else:
            userinfo = requests.get(
                FACEBOOK_USERINFO_URL,
                params={
                    "access_token": access_token,
                    "fields": "id,name,email,picture"
                }
            ).json()

            if "email" not in userinfo:
                return Response({"error": "Facebook token буруу"}, status=401)

            email = userinfo["email"]
            full_name = userinfo.get("name", "")
            profile_image = userinfo.get("picture", {}).get("data", {}).get("url")

        # ===== USER CHECK =====
        user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )

        # ===== REGISTER IF NOT EXISTS =====
        if not user:
            user = execute_insert(
                """
                INSERT INTO users (email, full_name, user_type, is_verified, is_active, profile_image_url)
                VALUES (%s, %s, 'customer', true, true, %s)
                RETURNING id, email, full_name, user_type, is_verified
                """,
                (email, full_name, profile_image)
            )

            execute_insert(
                """
                INSERT INTO customer_profiles (user_id)
                VALUES (%s)
                """,
                (user["id"],)
            )

        # ===== JWT =====
        token = create_access_token(user["id"], user["email"])

        return Response({
            "message": "Social login амжилттай",
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "full_name": user["full_name"],
                "user_type": user["user_type"],
                "is_verified": user["is_verified"],
            },
            "access_token": token
        }, status=200)