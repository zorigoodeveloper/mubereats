import time, random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..auth import JWTAuthentication
from ..database import execute_query, execute_insert

class RestaurantReviewView(APIView):
    authentication_classes = [JWTAuthentication]
    # GET хүсэлтийг хэн ч харж болно (AllowAny), POST-г зөвхөн нэвтэрсэн хэрэглэгч (IsAuthenticated)
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        resID = request.query_params.get("resID")
        if not resID:
            return Response({"error": "resID шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = execute_query("""
            SELECT r."resID", r."foodID", f."foodName", r."userID", u."full_name" as "userName", r."review" as rating, r."comment", r."date" as created_at, r."commID" as id
            FROM tbl_review_rating r
            LEFT JOIN users u ON u.id = r."userID"
            LEFT JOIN tbl_food f ON f."foodID" = r."foodID"
            WHERE r."resID" = %s
            ORDER BY r."date" DESC
        """, (resID,))

        if reviews:
            for r in reviews:
                if r.get("foodID") is None:
                    r.pop("foodID", None)
                    r.pop("foodName", None)

        return Response({"reviews": reviews or []}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        resID = data.get("resID")
        rating = data.get("rating")
        comment = data.get("comment", "")
        user_id = request.user['id']  

        if not resID or not rating:
            return Response({"error": "resID болон rating шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError
        except ValueError:
            return Response({"error": "Үнэлгээ 1-ээс 5-ын хооронд бүхэл тоо байх ёстой"}, status=status.HTTP_400_BAD_REQUEST)

        comm_id = int(time.time()) + random.randint(1, 100000)
        review = execute_insert("""
            INSERT INTO tbl_review_rating ("commID", "resID", "userID", "review", "comment", "date")
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING "commID"
        """, (comm_id, resID, user_id, rating, comment))

        return Response({"message": "Үнэлгээ амжилттай нэмэгдлээ", "reviewID": review['commID']}, status=status.HTTP_201_CREATED)


class DriverReviewView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        workerID = request.query_params.get("workerID")
        if not workerID:
            return Response({"error": "workerID шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = execute_query("""
            SELECT r."commID" as id, r."userID", u."full_name" as "userName", r."review" as rating, r."comment", r."date" as created_at
            FROM tbl_review_rating r
            LEFT JOIN users u ON u.id = r."userID"
            WHERE r."workerID" = %s
            ORDER BY r."date" DESC
        """, (workerID,))

        return Response({"reviews": reviews or []}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        workerID = data.get("workerID")
        rating = data.get("rating")
        comment = data.get("comment", "")
        user_id = request.user['id']

        if not workerID or not rating:
            return Response({"error": "workerID болон rating шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        comm_id = int(time.time()) + random.randint(1, 100000)
        review = execute_insert("""
            INSERT INTO tbl_review_rating ("commID", "workerID", "userID", "review", "comment", "date")
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING "commID"
        """, (comm_id, workerID, user_id, rating, comment))

        return Response({"message": "Үнэлгээ амжилттай нэмэгдлээ", "reviewID": review['commID']}, status=status.HTTP_201_CREATED)


class FoodReviewView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        foodID = request.query_params.get("foodID")
        if not foodID:
            return Response({"error": "foodID шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = execute_query("""
            SELECT r."commID" as id, r."foodID", r."userID", u."full_name" as "userName", r."review" as rating, r."comment", r."date" as created_at
            FROM tbl_review_rating r
            LEFT JOIN users u ON u.id = r."userID"
            WHERE r."foodID" = %s
            ORDER BY r."date" DESC
        """, (foodID,))

        return Response({"reviews": reviews or []}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        resID = data.get("resID")
        foodID = data.get("foodID")
        rating = data.get("rating")
        comment = data.get("comment", "")
        user_id = request.user['id']

        if not resID or not foodID or not rating:
            return Response({"error": "resID, foodID болон rating шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError
        except ValueError:
            return Response({"error": "Үнэлгээ 1-ээс 5-ын хооронд бүхэл тоо байх ёстой"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify food belongs to restaurant
        food_info = execute_query('SELECT "resID" FROM tbl_food WHERE "foodID" = %s', (foodID,), fetch_one=True)
        if not food_info:
            return Response({"error": "Хоол олдсонгүй"}, status=status.HTTP_404_NOT_FOUND)
        
        if str(food_info['resID']) != str(resID):
            return Response({"error": "Сонгосон хоол тухайн ресторанд хамааралгүй байна"}, status=status.HTTP_400_BAD_REQUEST)

        comm_id = int(time.time()) + random.randint(1, 100000)
        review = execute_insert("""
            INSERT INTO tbl_review_rating ("commID", "foodID", "resID", "userID", "review", "comment", "date")
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING "commID"
        """, (comm_id, foodID, resID, user_id, rating, comment))

        return Response({"message": "Үнэлгээ амжилттай нэмэгдлээ", "reviewID": review['commID']}, status=status.HTTP_201_CREATED)
