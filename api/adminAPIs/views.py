
# views/admin_users.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from ..database import execute_query, execute_update
from .auth import JWTAuthentication, verify_password, create_access_token
from .permissions import IsAdminUserCustom
from datetime import datetime, timedelta

# Бүх админ хэрэглэгч авах
class AdminUserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        users = execute_query("""
            SELECT id, email, username, is_active
            FROM auth_user
            ORDER BY id DESC
        """)
        return Response(users)


# Нэг админ хэрэглэгчийн мэдээлэл
class AdminUserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request, user_id):
        user = execute_query("""
            SELECT id, email, username,
                   is_active
            FROM auth_user
            WHERE id = %s
        """, (user_id,), fetch_one=True)

        if not user:
            return Response({'error': 'User not found'}, status=404)
        return Response(user)


# Админ update
class AdminUserUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def put(self, request, user_id):
        data = request.data
        rowcount = execute_update("""
            UPDATE auth_user
            SET username = %s,
                is_active = %s
            WHERE id = %s
        """, (
            data.get('username'),
            data.get('is_active'),
            user_id
        ))

        if rowcount == 0:
            return Response({'error': 'User not found'}, status=404)
        return Response({'message': 'User updated successfully'})


# Админ soft delete
class AdminUserDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def delete(self, request, user_id):
        rowcount = execute_update("""
            UPDATE auth_user
            SET is_active = FALSE
            WHERE id = %s
        """, (user_id,))

        if rowcount == 0:
            return Response({'error': 'User not found'}, status=404)
        return Response({'message': 'User deactivated'})


# Admin login
class AdminSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email болон password заавал'}, status=400)

        user = execute_query(
            "SELECT * FROM auth_user WHERE email = %s",
            (email,),
            fetch_one=True
        )

        if not user:
            return Response({'error': 'Хэрэглэгч олдсонгүй'}, status=401)

        if not verify_password(password, user['password']):
            return Response({'error': 'Нууц үг буруу'}, status=401)

        if not user['is_active']:
            return Response({'error': 'Хэрэглэгч идэвхгүй байна'}, status=403)

        token = create_access_token(user['id'], user['email'])

        return Response({
            'message': 'Амжилттай нэвтэрлээ',
            'access_token': token,
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'full_name': user.get('full_name')
            }
        })

class AdminApproveRestaurantView(APIView):
    authentication_classes = [AllowAny]
    permission_classes = [IsAdminUserCustom]

    def post(self, request, resID):
        rowcount = execute_update(
            'UPDATE "tbl_restaurant" SET "status"=TRUE WHERE "resID"=%s',
            (resID,)
        )
        if rowcount == 0:
            return Response({"error": "Ресторан олдсонгүй"}, status=404)
        return Response({"message": "Ресторан зөвшөөрсөн"})


class AdminApproveDriverView(APIView):
    authentication_classes = [AllowAny]
    permission_classes = [IsAdminUserCustom]

    def post(self, request, workerID):
        rowcount = execute_update(
            'UPDATE "tbl_worker" SET "status"=TRUE WHERE "workerID"=%s', (workerID,)
        )
        if rowcount == 0:
            return Response({"error": "Жолооч олдсонгүй"}, status=404)
        return Response({"message": "Жолоочийг зөвшөөрсөн"})

# Бүх рестораны бүртгэл харах
class AdminRestaurantListView(APIView):
    authentication_classes = [AllowAny]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        restaurants = execute_query("""
            SELECT "resID", "resName", "catID", "email", "phone",
                   "status", "openTime", "closeTime", "description"
            FROM "tbl_restaurant"
            ORDER BY "resID" DESC
        """)
        return Response(restaurants)


# Бүх жолоочийн бүртгэл харах
class AdminDriverListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        drivers = execute_query("""
            SELECT "workerID", "workerName", "email", "phone",
                   "vehicleType", "vehicleReg", "tuluv"
            FROM "tbl_worker"
            ORDER BY "workerID" DESC
        """)
        return Response(drivers)


# Зөвшөөрөл хүлээж байгаа рестораны бүртгэл
class AdminPendingRestaurantListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        restaurants = execute_query("""
            SELECT "resID", "resName", "catID", "email", "phone",
                "status", "openTime", "closeTime", "description"
            FROM "tbl_restaurant"
            WHERE "status" = 'false'
            ORDER BY "resID" DESC
        """)
        return Response(restaurants)

# Зөвшөөрөл хүлээж байгаа жолоочийн бүртгэл
class AdminPendingDriverListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        drivers = execute_query("""
            SELECT "workerID", "workerName", "email", "phone",
                   "vehicleType", "vehicleReg", "tuluv"
            FROM "tbl_worker"
            WHERE "tuluv" = 'false'
            ORDER BY "workerID" DESC
        """)
        return Response(drivers)


# -------------------------------------------------------------------------
# Бүх купон харах
class CouponListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        coupons = execute_query("""
            SELECT "ID", "code", "percent", "duration", "active"
            FROM "tbl_coupon"
            ORDER BY "ID" DESC
        """)
        return Response(coupons)


# Нэг купон харах
class CouponDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request, coupon_id):
        coupon = execute_query("""
            SELECT "ID", "code", "percent", "duration", "active"
            FROM "tbl_coupon"
            WHERE "ID" = %s
        """, (coupon_id,), fetch_one=True)

        if not coupon:
            return Response({'error': 'Coupon not found'}, status=404)
        return Response(coupon)


# Купон нэмэх
class CouponCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def post(self, request):
        data = request.data
        execute_update("""
            INSERT INTO "tbl_coupon" ("code", "percent", "duration", "active")
            VALUES (%s, %s, %s, %s)
        """, (
            data.get('code'),
            data.get('percent'),
            data.get('duration'),
            data.get('active', 'TRUE')
        ))
        return Response({'message': 'Coupon created successfully'})


# Купон update
class CouponUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def put(self, request, coupon_id):
        data = request.data
        rowcount = execute_update("""
            UPDATE "tbl_coupon"
            SET "code" = %s,
                "percent" = %s,
                "duration" = %s,
                "active" = %s
            WHERE "ID" = %s
        """, (
            data.get('code'),
            data.get('percent'),
            data.get('duration'),
            data.get('active'),
            coupon_id
        ))

        if rowcount == 0:
            return Response({'error': 'Coupon not found'}, status=404)
        return Response({'message': 'Coupon updated successfully'})


# Купон soft delete
class CouponDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def delete(self, request, coupon_id):
        rowcount = execute_update("""
            UPDATE "tbl_coupon"
            SET "active" = 'FALSE'
            WHERE "ID" = %s
        """, (coupon_id,))

        if rowcount == 0:
            return Response({'error': 'Coupon not found'}, status=404)
        return Response({'message': 'Coupon deactivated'})
    

# statistic harah 
class AdminStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, IsAdminUserCustom]

    def get(self, request):
        today = datetime.utcnow().date()
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        last_half_year = today - timedelta(days=182)
        last_year = today - timedelta(days=365)

        stats = {}

        # Restaurant бүртгэл
        stats['restaurants'] = {
            'week': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True
            )['count'],
            'month': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True
            )['count'],
            'half_year': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True
            )['count'],
            'year': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True
            )['count'],
        }

        # Driver бүртгэл
        stats['drivers'] = {
            'week': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True
            )['count'],
            'month': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True
            )['count'],
            'half_year': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True
            )['count'],
            'year': execute_query(
                'SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True
            )['count'],
        }

        # Хэрэглэгч бүртгэл
        stats['customers'] = {
            'week': execute_query(
                'SELECT COUNT(*) AS count FROM "users"', fetch_one=True
            )['count'],
            'month': execute_query(
                'SELECT COUNT(*) AS count FROM "users"', fetch_one=True
            )['count'],
            'half_year': execute_query(
                'SELECT COUNT(*) AS count FROM "users"', fetch_one=True
            )['count'],
            'year': execute_query(
                'SELECT COUNT(*) AS count FROM "users"', fetch_one=True
            )['count'],
        }

        # Нийт борлуулалт tbl_orderfood дээр
        stats['sales'] = {
            'week': execute_query(
                'SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True
            )['total'],
            'month': execute_query(
                'SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True
            )['total'],
            'half_year': execute_query(
                'SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True
            )['total'],
            'year': execute_query(
                'SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True
            )['total'],
        }

        return Response(stats)