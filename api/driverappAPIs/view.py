from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import WorkerSerializer, SignInSerializer, DeliveryActionSerializer, DeliveryStatusSerializer  
from ..database import execute_query, execute_insert
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication


# -------------------------
# AUTH
# -------------------------

class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        existing_worker = execute_query(
            """
            SELECT "workerID"
            FROM "tbl_worker"
            WHERE "email" = %s OR "phone" = %s
            """,
            (data["email"], data["phone"]),
            fetch_one=True
        )

        if existing_worker:
            return Response(
                {"error": "Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна"},
                status=status.HTTP_400_BAD_REQUEST
            )

        password_hash = hash_password(data["password"])

        worker = execute_insert(
            """
            INSERT INTO "tbl_worker"
            ("workerName", "phone", "email", "password_hash", "vehicleType", "vehicleReg", "image")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING "workerID", "workerName", "phone", "email", "vehicleType", "vehicleReg", "image"
            """,
            (
                data["workerName"],
                data["phone"],
                data["email"],
                password_hash,
                data.get("vehicleType"),
                data.get("vehicleReg"),
                data.get("image"),  # 👈 шинэ
            )
        )

        access_token = create_access_token(
            user_id=str(worker["workerID"]),
            email=worker["email"]
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
                    "vehicleReg": worker["vehicleReg"],
                    "image": worker.get("image"),  # 👈 шинэ
                },
                "access_token": access_token,
            },
            status=status.HTTP_201_CREATED
        )


class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        worker = request.user
        worker_id = worker["id"]

        # 1) Get current profile (so we can merge fields safely)
        current = execute_query(
            """
            SELECT "workerID", "workerName", "phone", "email", "vehicleType", "vehicleReg", "image"
            FROM "tbl_worker"
            WHERE "workerID" = %s
            """,
            (worker_id,),
            fetch_one=True
        )

        if not current:
            return Response({"error": "Профайл олдсонгүй"}, status=status.HTTP_404_NOT_FOUND)

        # 2) If phone/email is being changed, check duplicates
        new_email = request.data.get("email", current["email"])
        new_phone = request.data.get("phone", current["phone"])

        dup = execute_query(
            """
            SELECT "workerID"
            FROM "tbl_worker"
            WHERE ("email" = %s OR "phone" = %s) AND "workerID" <> %s
            """,
            (new_email, new_phone, worker_id),
            fetch_one=True
        )
        if dup:
            return Response(
                {"error": "Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Merge fields (only update what's provided)
        workerName = request.data.get("workerName", current["workerName"])
        phone = new_phone
        email = new_email
        vehicleType = request.data.get("vehicleType", current["vehicleType"])
        vehicleReg = request.data.get("vehicleReg", current["vehicleReg"])
        image = request.data.get("image", current["image"])

        # 4) Update + RETURNING
        updated = execute_insert(
            """
            UPDATE "tbl_worker"
            SET "workerName" = %s,
                "phone" = %s,
                "email" = %s,
                "vehicleType" = %s,
                "vehicleReg" = %s,
                "image" = %s
            WHERE "workerID" = %s
            RETURNING "workerID", "workerName", "phone", "email", "vehicleType", "vehicleReg", "image"
            """,
            (workerName, phone, email, vehicleType, vehicleReg, image, worker_id)
        )

        return Response(
            {
                "message": "Профайл амжилттай шинэчлэгдлээ",
                "worker": {
                    "workerID": str(updated["workerID"]),
                    "workerName": updated["workerName"],
                    "email": updated["email"],
                    "phone": updated["phone"],
                    "vehicleType": updated["vehicleType"],
                    "vehicleReg": updated["vehicleReg"],
                    "image": updated.get("image"),
                },
            },
            status=status.HTTP_200_OK
        )

    def put(self, request):
        """
        Full update (requires all fields).
        If you don't want strict full update, you can just call patch internally.
        """
        return self.patch(request)

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
            (data["email"],),
            fetch_one=True
        )

        if not worker or not verify_password(data["password"], worker["password_hash"]):
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
                    "vehicleReg": worker["vehicleReg"],
                },
                "access_token": access_token,
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        worker = request.user  # must contain {"id": <workerID>, ...}

        profile = execute_query(
            """
            SELECT 
                "workerID",
                "workerName",
                "phone",
                "email",
                "vehicleType",
                "vehicleReg",
                "image"
            FROM "tbl_worker"
            WHERE "workerID" = %s
            """,
            (worker["id"],),
            fetch_one=True
        )


        if not profile:
            return Response({"error": "Профайл олдсонгүй"}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "worker": {
                    "workerID": str(profile["workerID"]),
                    "workerName": profile["workerName"],
                    "email": profile["email"],
                    "phone": profile["phone"],
                    "vehicleType": profile["vehicleType"],
                    "vehicleReg": profile["vehicleReg"],
                }
            },
            status=status.HTTP_200_OK
        )


# -------------------------
# ORDERS (DRIVER)
# -------------------------

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


class DeliveryView(APIView):
    """
    POST /auth/driver/orders/delivery_status
    Body: {"orderID": 123, "status": "accept" | "picked_up" | "delivered"}
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        worker = request.user

        serializer = DeliveryActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.validated_data["orderID"]
        action = serializer.validated_data["status"]

        # Ensure order exists
        order = execute_query(
            """
            SELECT "orderID"
            FROM "tbl_order"
            WHERE "orderID" = %s
            """,
            (order_id,),
            fetch_one=True
        )
        if not order:
            return Response({"error": "Захиалга олдсонгүй"}, status=status.HTTP_404_NOT_FOUND)

        # ACCEPT
        if action == "accept":
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
                return Response({"error": "Энэ захиалга аль хэдийн хүргэгчтэй"}, status=status.HTTP_400_BAD_REQUEST)

            delivery = execute_insert(
                """
                INSERT INTO "tbl_deliver" ("orderID", "workerID", "status", "startdate")
                VALUES (%s, %s, %s, NOW()::date)
                RETURNING "delID", "orderID", "workerID", "status", "startdate"
                """,
                (order_id, worker["id"], "Захиалга авлаа")
            )

            execute_insert(
                """
                UPDATE "tbl_order"
                SET "status" = %s
                WHERE "orderID" = %s
                """,
                ("accepted", order_id)
            )

            return Response(
                {"message": "Захиалгыг амжилттай авлаа", "delivery": delivery},
                status=status.HTTP_201_CREATED
            )

        # PICKED UP
        if action == "picked_up":
            updated = execute_insert(
                """
                UPDATE "tbl_deliver"
                SET "status" = %s
                WHERE "orderID" = %s
                  AND "workerID" = %s
                RETURNING "delID"
                """,
                ("Хүргэлтэд гарлаа", order_id, worker["id"])
            )
            if not updated:
                return Response({"error": "Хүргэлт олдсонгүй эсвэл зөвшөөрөлгүй"}, status=status.HTTP_403_FORBIDDEN)

            return Response({"message": "Хүргэлтэд гарлаа"}, status=status.HTTP_200_OK)

        # DELIVERED
        updated = execute_insert(
            """
            UPDATE "tbl_deliver"
            SET "status" = %s,
                "enddate" = NOW()::date
            WHERE "orderID" = %s
              AND "workerID" = %s
            RETURNING "delID"
            """,
            ("Дууссан", order_id, worker["id"])
        )
        if not updated:
            return Response({"error": "Хүргэлт олдсонгүй эсвэл зөвшөөрөлгүй"}, status=status.HTTP_403_FORBIDDEN)

        execute_insert(
            """
            UPDATE "tbl_order"
            SET "status" = %s
            WHERE "orderID" = %s
            """,
            ("delivered", order_id)
        )

        return Response({"message": "Хүргэлт амжилттай дууслаа"}, status=status.HTTP_200_OK)

class UpdateDeliveryStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        worker = getattr(request, "worker", None) or request.user
        if not worker:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = DeliveryStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.validated_data["orderID"]
        status_id = serializer.validated_data["statusID"]

        # 1️⃣ Захиалга байгаа эсэх
        order = execute_query(
            """
            SELECT "orderID"
            FROM "tbl_order"
            WHERE "orderID" = %s
            """,
            (order_id,),
            fetch_one=True
        )
        if not order:
            return Response(
                {"error": "Захиалга олдсонгүй"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ StatusID → statusName авах
        status_row = execute_query(
            """
            SELECT "statusName"
            FROM "tbl_delivery_status"
            WHERE "statusID" = %s
            """,
            (status_id,),
            fetch_one=True
        )
        if not status_row:
            return Response(
                {"error": "Буруу statusID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        status_name = status_row["statusName"]

        # 3️⃣ tbl_order.status update
        execute_insert(
            """
            UPDATE "tbl_order"
            SET "status" = %s
            WHERE "orderID" = %s
            """,
            (status_name, order_id)
        )

        return Response(
            {
                "message": "Захиалгын төлөв амжилттай шинэчлэгдлээ",
                "orderID": order_id,
                "statusID": status_id,
                "status": status_name
            },
            status=status.HTTP_200_OK
        )


