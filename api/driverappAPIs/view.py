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
        serializer = WorkerSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Check existing worker
        existing_worker = execute_query(
            """
            SELECT "workerID"
            FROM "tbl_worker"
            WHERE "email" = %s OR "phone" = %s
            """,
            (data['email'], data['phone']),
            fetch_one=True
        )

        if existing_worker:
            return Response(
                {"error": "Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна"},
                status=status.HTTP_400_BAD_REQUEST
            )

        password_hash = hash_password(data['password'])

        worker = execute_insert(
            """
            INSERT INTO "tbl_worker"
            ("workerName", "phone", "email", "password_hash", "vehicleType", "vehicleReg")
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING "workerID", "workerName", "phone", "email",
                      "vehicleType", "vehicleReg"
            """,
            (
                data['workerName'],
                data['phone'],
                data['email'],
                password_hash,
                data.get('vehicleType'),
                data.get('vehicleReg')
            )
        )

        access_token = create_access_token(
            user_id=str(worker['workerID']),
            email=worker['email']
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
                },
                "access_token": access_token
            },
            status=status.HTTP_201_CREATED
        )
class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        worker = execute_query(
            """
            SELECT "workerID", "workerName", "phone", "email",
                   "password_hash", "vehicleType", "vehicleReg"
            FROM "tbl_worker"
            WHERE "email" = %s
            """,
            (data['email'],),
            fetch_one=True
        )

        if not worker or not verify_password(data['password'], worker['password_hash']):
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
        worker = request.user 

        profile = execute_query(
            """
            SELECT "workerID", "workerName", "phone",   "email",
                   "vehicleType", "vehicleReg"
            FROM "tbl_worker"
            WHERE "workerID" = %s
            """,
            (worker["id"],),
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
    
class AvailableOrdersView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = execute_query(
            """
            SELECT o."orderID", o."userID", o."date", o."location", o."status"
            FROM "tbl_order" o
            LEFT JOIN "tbl_deliver" d ON d."orderID" = o."orderID"
            WHERE d."orderID" IS NULL
            ORDER BY o."date" DESC
            """
        )
        return Response({"orders": orders}, status=status.HTTP_200_OK)


class AcceptOrderView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        worker = request.user  # worker["id"] = workerID

        # already taken?
        existing = execute_query(
            """
            SELECT "delID"
            FROM "tbl_deliver"
            WHERE "orderID" = %s
            """,
            (order_id,),
            fetch_one=True
        )
        if existing:
            return Response(
                {"error": "Энэ захиалга аль хэдийн хүргэгчтэй болсон байна"},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery = execute_insert(
            """
            INSERT INTO "tbl_deliver" ("orderID", "workerID", "status", "startdate")
            VALUES (%s, %s, %s, NOW()::date)
            RETURNING "delID", "orderID", "workerID", "status", "startdate"
            """,
            (order_id, worker["id"], "Захиалга авлаа")
        )

        return Response(
            {"message": "Захиалгыг авлаа", "delivery": delivery},
            status=status.HTTP_201_CREATED
        )


class MyOrdersView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        worker = request.user

        rows = execute_query(
            """
            SELECT o."orderID", o."userID", o."date", o."location",
                   d."delID", d."status", d."startdate", d."enddate"
            FROM "tbl_deliver" d
            JOIN "tbl_order" o ON o."orderID" = d."orderID"
            WHERE d."workerID" = %s
            ORDER BY d."delID" DESC
            """,
            (worker["id"],)
        )

        return Response({"orders": rows}, status=status.HTTP_200_OK)


class UpdateDeliveryStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        worker = request.user
        new_status = request.data.get("status")

        allowed = ["Захиалга авлаа", "Хүргэлтэд гарлаа", "Очиж байна", "Дууссан"]
        if new_status not in allowed:
            return Response({"error": "Буруу төлөв"}, status=status.HTTP_400_BAD_REQUEST)

        # If delivered -> set enddate
        if new_status == "Дууссан":
            updated = execute_insert(
                """
                UPDATE "tbl_deliver"
                SET "status" = %s,
                    "enddate" = NOW()::date
                WHERE "orderID" = %s
                  AND "workerID" = %s
                RETURNING "delID"
                """,
                (new_status, order_id, worker["id"])
            )
        else:
            updated = execute_insert(
                """
                UPDATE "tbl_deliver"
                SET "status" = %s
                WHERE "orderID" = %s
                  AND "workerID" = %s
                RETURNING "delID"
                """,
                (new_status, order_id, worker["id"])
            )

        if not updated:
            return Response(
                {"error": "Хүргэлт олдсонгүй эсвэл энэ захиалга танд хамаарахгүй"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({"message": "Төлөв шинэчлэгдлээ"}, status=status.HTTP_200_OK)
