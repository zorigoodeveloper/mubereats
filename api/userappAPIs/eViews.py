

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from django.utils.datastructures import MultiValueDictKeyError

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

class RestaurantListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    distance_km = serializers.FloatField(allow_null=True)


class NearbyOrSearchRestaurantsAPIView(APIView):
    """
    Хайлтгүй бол → ойролцоох ресторануудыг харуулна
    Хайлттай бол → нэрээр хайгаад ойр байх дарааллаар + зайтай харуулна
    
    Жишээ:
    GET /api/restaurants/nearby/?lat=47.918&lon=106.917          → ойролцоох 10 ресторан
    GET /api/restaurants/nearby/?q=nomad&lat=47.918&lon=106.917  → "nomad" агуулсан ресторануудыг ойр байхаар нь
    """
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        limit = int(request.GET.get("limit", 12))

        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
        except (ValueError, TypeError, MultiValueDictKeyError):
            return Response(
                {"error": "lat болон lon заавал өгөх ёстой (тоо утга)"},
                status=400
            )

        # Earth radius (km)
        R = 6371.0

        base_query = """
            SELECT 
                r."resID" AS id,
                r."resName" AS name,
                (6371 * acos(
                    cos(radians(%s)) 
                    * cos(radians(r."lat")) 
                    * cos(radians(r."lng") - radians(%s)) 
                    + sin(radians(%s)) 
                    * sin(radians(r."lat"))
                )) AS distance_km
            FROM tbl_restaurant r
            WHERE r."lat" IS NOT NULL 
              AND r."lng" IS NOT NULL
        """

        params = [lat, lon, lat]

        if q:
            base_query += """ 
                AND r."resName" ILIKE %s
            """
            params.append(f"%{q}%")

        base_query += """
            ORDER BY distance_km
            LIMIT %s
        """
        params.append(limit)

        results = execute_query(base_query, tuple(params))

        data = [
            {
                "id": row["id"],
                "name": row["name"],
                "distance_km": round(row["distance_km"], 2) if row["distance_km"] is not None else None
            }
            for row in results
        ]

        serializer = RestaurantListSerializer(data, many=True)
        return Response({
            "results": serializer.data,
            "searched_term": q if q else None,
            "user_location": {"lat": lat, "lon": lon},
            "count": len(data)
        })