from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import WorkerSerializer, SignInSerializer
from ..database import execute_query, execute_insert
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication

class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        worker_name = data.get("workerName")
        phone = data.get("phone")
        email = data.get("email")
        password = data.get("password")

        if not worker_name or not phone or not email or not password:
            return Response(
                {"error": "workerName, phone, email, password заавал шаардлагатай"},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_worker = execute_query(
            """
            SELECT "workerID"
            FROM "tbl_worker"
            WHERE "email" = %s OR "phone" = %s
            """,
            (email, phone),
            fetch_one=True
        )

        if existing_worker:
            return Response(
                {"error": "Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна"},
                status=status.HTTP_400_BAD_REQUEST
            )

        password_hash = hash_password(password)

        worker = execute_insert(
            """
            INSERT INTO "tbl_worker"
            ("workerName", "phone", "email","password_hash", "vehicleType", "vehicleReg")
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING "workerID", "workerName", "phone", "email",
                      "vehicleType", "vehicleReg"
            """,
            (
            data['workerName'],
            data['phone'], 
            data['email'], 
            password_hash,
            data.get('vehicleType', None), 
            data.get('vehicleReg', None)
            )
        )

        return Response(
            {
                "message": "Амжилттай бүртгэгдлээ",
                "worker": {
                    "workerID": str(worker["workerID"]),
                    "workerName": worker["workerName"],
                    "email": worker["email"],
                    "phone": worker["phone"],
                    "vehicleType": worker["vehicleType"],
                    "vehicleReg": worker["vehicleReg"]
                }
            },
            status=status.HTTP_201_CREATED
        )

class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        identifier = data.get("email")
        password = data.get("password")

        if not identifier or not password:
            return Response(
                {"error": "email болон password заавал шаардлагатай"},
                status=status.HTTP_400_BAD_REQUEST
            )

        worker = execute_query(
            """
            SELECT "workerID", "workerName", "phone", "email",
                   "password_hash", "vehicleType", "vehicleReg"
            FROM "tbl_worker"
            WHERE "email" = %s
            """,
            (identifier,),
            fetch_one=True
        )

        if not worker:
            return Response(
                {"error": "Имэйл эсвэл нууц үг буруу байна"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not verify_password(password, worker["password_hash"]):
            return Response(
                {"error": "Имэйл эсвэл нууц үг буруу байна"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = create_access_token(
            user_id=str(worker["workerID"]),
            email=worker["email"]
        )

        return Response(
            {
                "message": "Амжилттай нэвтэрлээ",
                "worker": {
                    "workerID": str(worker["workerID"]),
                    "workerName": worker["workerName"],
                    "email": worker["email"],
                    "phone": worker["phone"],
                    "vehicleType": worker["vehicleType"],
                    "vehicleReg": worker["vehicleReg"]
                },
                "access_token": access_token
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user 

        profile = execute_query(
            """
            SELECT "workerID", "workerName", "phone", "email",
                   "vehicleType", "vehicleReg"
            FROM "tbl_worker"
            WHERE "workerID" = %s
            """,
            (user["id"],),
            fetch_one=True
        )

        if not profile:
            return Response(
                {"error": "Профайл олдсонгүй"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "worker": {
                    "workerID": str(profile["workerID"]),
                    "workerName": profile["workerName"],
                    "email": profile["email"],
                    "phone": profile["phone"],
                    "vehicleType": profile["vehicleType"],
                    "vehicleReg": profile["vehicleReg"]
                }
            },
            status=status.HTTP_200_OK
        )

