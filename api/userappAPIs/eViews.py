from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from ..database import execute_query

class RestaurantSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    foods = serializers.ListField(child=serializers.CharField())

class RestaurantSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if not q:
            return Response([])

        # Restaurant search
        restaurants = execute_query(
            """
            SELECT DISTINCT
                r."resID",
                r."resName"
            FROM tbl_restaurant r
            LEFT JOIN tbl_food f ON f."resID" = r."resID"
            WHERE
                r."resName" ILIKE %s
                OR f."foodName" ILIKE %s
            ORDER BY r."resName"
            """,
            (f"%{q}%", f"%{q}%")
        )


        results = []
        for r in restaurants:
            # Foods query
            foods = execute_query(
                'SELECT "foodName" FROM tbl_food WHERE "resID" = %s AND "foodName" ILIKE %s',
                (r['resID'], f"%{q}%")
            )

            results.append({
                "id": r['resID'],
                "name": r['resName'],
                "foods": [f['name'] for f in foods] if foods else []
            })

        serializer = RestaurantSearchSerializer(results, many=True)
        return Response(serializer.data)
