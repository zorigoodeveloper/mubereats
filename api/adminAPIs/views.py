from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from datetime import datetime, timedelta

from ..database import execute_insert, execute_query, execute_update
from .auth import JWTAuthentication, verify_password, create_access_token
from .permissions import IsAdminUserCustom


# ----------------------------
# ADMIN USERS
# ----------------------------

class AdminUserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        users = execute_query("""
            SELECT id, email, username, is_active
            FROM auth_user
            ORDER BY id DESC
        """)
        return Response(users, status=200)


class AdminUserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request, user_id):
        user = execute_query("""
            SELECT id, email, username, is_active
            FROM auth_user
            WHERE id = %s
        """, (user_id,), fetch_one=True)

        if not user:
            return Response({'error': 'User not found'}, status=404)
        return Response(user, status=200)


class AdminUserUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def put(self, request, user_id):
        data = request.data
        rowcount = execute_update("""
            UPDATE auth_user
            SET username = %s,
                is_active = %s
            WHERE id = %s
        """, (
            data.get('username'),
            data.get('is_active', True),
            user_id
        ))

        if rowcount == 0:
            return Response({'error': 'User not found'}, status=404)
        return Response({'message': 'User updated successfully'}, status=200)


class AdminUserDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def delete(self, request, user_id):
        rowcount = execute_update("""
            UPDATE auth_user
            SET is_active = FALSE
            WHERE id = %s
        """, (user_id,))

        if rowcount == 0:
            return Response({'error': 'User not found'}, status=404)
        return Response({'message': 'User deactivated'}, status=200)


class AdminSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email болон password заавал'}, status=400)

        user = execute_query(
            'SELECT id, email, password, is_active, username FROM auth_user WHERE email = %s',
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
                'username': user.get('username'),
            }
        }, status=200)


# ----------------------------
# RESTAURANTS (ADMIN APPROVAL)
# ----------------------------

class AdminApproveRestaurantView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request, resID):
        rowcount = execute_update(
            'UPDATE "tbl_restaurant" SET "status"=TRUE WHERE "resID"=%s',
            (resID,)
        )
        if rowcount == 0:
            return Response({"error": "Ресторан олдсонгүй"}, status=404)
        return Response({"message": "Ресторан зөвшөөрсөн"}, status=200)


class AdminRestaurantListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        restaurants = execute_query("""
            SELECT "resID", "resName", "catID", "email", "phone",
                   "status", "openTime", "closeTime", "description"
            FROM "tbl_restaurant"
            ORDER BY "resID" DESC
        """)
        return Response(restaurants, status=200)


class AdminPendingRestaurantListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        restaurants = execute_query("""
            SELECT "resID", "resName", "catID", "email", "phone",
                   "status", "openTime", "closeTime", "description"
            FROM "tbl_restaurant"
            WHERE "status" = FALSE
            ORDER BY "resID" DESC
        """)
        return Response(restaurants, status=200)


# ----------------------------
# DRIVERS (ADMIN APPROVAL)
# ----------------------------
class AdminPendingWorkersView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        rows = execute_query("""
            SELECT "workerID",
                   "workerName",
                   "phone",
                   "email",
                   "vehicleType",
                   "vehicleReg",
                   "isApproved"
            FROM "tbl_worker"
            WHERE "isApproved" = FALSE
            ORDER BY "workerID" DESC
        """)
        return Response({"pending": rows}, status=200)

class AdminApproveWorkerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        worker_id = request.data.get("workerID")
        if not worker_id:
            return Response({"error": "workerID шаардлагатай"}, status=400)

        updated = execute_insert("""
            UPDATE "tbl_worker"
            SET "isApproved" = TRUE,
                "approvedAt" = NOW()
            WHERE "workerID" = %s
            RETURNING "workerID","isApproved","approvedAt"
        """, (worker_id,))

        if not updated:
            return Response({"error": "Worker олдсонгүй"}, status=404)

        return Response(
            {"message": "Зөвшөөрлөө", "worker": updated},
            status=200
        )

class AdminRejectWorkerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        worker_id = request.data.get("workerID")
        if not worker_id:
            return Response({"error": "workerID шаардлагатай"}, status=400)

        deleted = execute_insert("""
            DELETE FROM "tbl_worker"
            WHERE "workerID" = %s
            RETURNING "workerID"
        """, (worker_id,))

        if not deleted:
            return Response({"error": "Worker олдсонгүй"}, status=404)

        return Response({"message": "Татгалзлаа"}, status=200)

# ----------------------------
# COUPONS
# ----------------------------

class CouponListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        coupons = execute_query("""
            SELECT "ID", "code", "percent", "duration", "active"
            FROM "tbl_coupon"
            ORDER BY "ID" DESC
        """)
        return Response(coupons, status=200)


class CouponDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request, coupon_id):
        coupon = execute_query("""
            SELECT "ID", "code", "percent", "duration", "active"
            FROM "tbl_coupon"
            WHERE "ID" = %s
        """, (coupon_id,), fetch_one=True)

        if not coupon:
            return Response({'error': 'Coupon not found'}, status=404)
        return Response(coupon, status=200)


class CouponCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        data = request.data
        execute_update("""
            INSERT INTO "tbl_coupon" ("code", "percent", "duration", "active")
            VALUES (%s, %s, %s, %s)
        """, (
            data.get('code'),
            data.get('percent'),
            data.get('duration'),
            data.get('active', True)
        ))
        return Response({'message': 'Coupon created successfully'}, status=201)


class CouponUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

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
        return Response({'message': 'Coupon updated successfully'}, status=200)


class CouponDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def delete(self, request, coupon_id):
        rowcount = execute_update("""
            UPDATE "tbl_coupon"
            SET "active" = FALSE
            WHERE "ID" = %s
        """, (coupon_id,))

        if rowcount == 0:
            return Response({'error': 'Coupon not found'}, status=404)
        return Response({'message': 'Coupon deactivated'}, status=200)


# ----------------------------
# STATISTICS
# ----------------------------

class AdminStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        # Note: currently your queries ignore date range (week/month/year). Kept as-is.
        stats = {}

        stats['restaurants'] = {
            'week': execute_query('SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True)['count'],
            'month': execute_query('SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True)['count'],
            'half_year': execute_query('SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True)['count'],
            'year': execute_query('SELECT COUNT(*) AS count FROM "tbl_restaurant"', fetch_one=True)['count'],
        }

        stats['drivers'] = {
            'week': execute_query('SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True)['count'],
            'month': execute_query('SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True)['count'],
            'half_year': execute_query('SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True)['count'],
            'year': execute_query('SELECT COUNT(*) AS count FROM "tbl_worker"', fetch_one=True)['count'],
        }

        stats['customers'] = {
            'week': execute_query('SELECT COUNT(*) AS count FROM "users"', fetch_one=True)['count'],
            'month': execute_query('SELECT COUNT(*) AS count FROM "users"', fetch_one=True)['count'],
            'half_year': execute_query('SELECT COUNT(*) AS count FROM "users"', fetch_one=True)['count'],
            'year': execute_query('SELECT COUNT(*) AS count FROM "users"', fetch_one=True)['count'],
        }

        stats['sales'] = {
            'week': execute_query('SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True)['total'],
            'month': execute_query('SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True)['total'],
            'half_year': execute_query('SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True)['total'],
            'year': execute_query('SELECT COALESCE(SUM("price"),0) AS total FROM "tbl_orderfood"', fetch_one=True)['total'],
        }

        return Response(stats, status=200)
