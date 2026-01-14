

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import serializers

from ..database import execute_query


# =========================
# SERIALIZERS
# =========================

class RestaurantSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class FoodSearchSerializer(serializers.Serializer):
    food_id = serializers.IntegerField()
    food_name = serializers.CharField()
    restaurant = serializers.DictField()


# =========================
# RESTAURANT SEARCH (NAME ONLY)
# =========================

class RestaurantOnlySearchAPIView(APIView):
    """
    🔍 Restaurant name-аар л хайна
    жишээ: /api/search/restaurants/?q=nomads
    """
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if not q:
            return Response([])

        restaurants = execute_query(
            """
            SELECT
                "resID",
                "resName"
            FROM tbl_restaurant
            WHERE "resName" ILIKE %s
            ORDER BY "resName"
            """,
            (f"%{q}%",)
        )

        data = [
            {
                "id": r["resID"],
                "name": r["resName"],
            }
            for r in restaurants
        ]

        serializer = RestaurantSearchSerializer(data, many=True)
        return Response(serializer.data)


# =========================
# FOOD SEARCH (FOOD NAME ONLY)
# =========================

class FoodOnlySearchAPIView(APIView):
    """
    🍕 Food name-аар л хайна
    жишээ: /api/search/foods/?q=pizza
    """
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if not q:
            return Response([])

        foods = execute_query(
            """
            SELECT
                f."foodID",
                f."foodName",
                r."resID",
                r."resName"
            FROM tbl_food f
            JOIN tbl_restaurant r ON r."resID" = f."resID"
            WHERE f."foodName" ILIKE %s
            ORDER BY f."foodName"
            """,
            (f"%{q}%",)
        )

        data = [
            {
                "food_id": f["foodID"],
                "food_name": f["foodName"],
                "restaurant": {
                    "id": f["resID"],
                    "name": f["resName"],
                }
            }
            for f in foods
        ]

        serializer = FoodSearchSerializer(data, many=True)
        return Response(serializer.data)
