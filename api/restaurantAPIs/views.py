from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RestaurantSerializer, FoodSerializer, DrinkSerializer,
    PackageSerializer, PackageFoodSerializer, PackageDrinkSerializer,RestaurantCategorySerializer
)

from .serializers import BranchSerializer

# ===== Restaurant CRUD =====
class RestaurantCreateView(APIView):
    def post(self, request):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                # Restaurant нэмэх, resID-г автоматаар авах
                c.execute("""
                    INSERT INTO tbl_restaurant ("resName", "catID", "phone")
                    VALUES (%s, %s, %s)
                    RETURNING "resID"
                """, [d['resName'], d['catID'], d.get('phone','')])
                res_id = c.fetchone()[0]

            return Response({"message": "Restaurant added", "resID": res_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RestaurantListView(APIView):
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "resID","resName","catID","phone" FROM tbl_restaurant')
            rows = c.fetchall()
        data = [{"resID": r[0], "resName": r[1], "catID": r[2], "phone": r[3]} for r in rows]
        return Response(data, status=status.HTTP_200_OK)


class RestaurantUpdateView(APIView):
    def put(self, request, resID):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_restaurant
                    SET "resName"=%s, "catID"=%s, "phone"=%s
                    WHERE "resID"=%s
                """, [d['resName'], d['catID'], d.get('phone',''), resID])
            return Response({"message": "Restaurant updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RestaurantDeleteView(APIView):
    def delete(self, request, resID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_restaurant WHERE "resID"=%s', [resID])
        return Response({"message": "Restaurant deleted"}, status=status.HTTP_200_OK)


# ===== Food CRUD =====
class FoodCreateView(APIView):
    def post(self, request):
        s = FoodSerializer(data=request.data)
        if s.is_valid():
            d = s.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO food
                    (foodName, resID, catID, price, description, image)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, [d["foodName"], d["resID"], d["catID"], d["price"], d.get("description",""), d.get("image","")])
            return Response({"message": "Food added"}, status=status.HTTP_201_CREATED)
        return Response(s.errors, 400)

class FoodListView(APIView):
    def get(self, request):
        resID = request.query_params.get("resID")
        with connection.cursor() as c:
            c.execute("SELECT foodID, foodName, price, description, image FROM food WHERE resID=%s", [resID])
            rows = c.fetchall()
        return Response([{"foodID": r[0], "foodName": r[1], "price": r[2], "description": r[3], "image": r[4]} for r in rows])


# ===== Package CRUD =====
class PackageCreateView(APIView):
    def post(self, request):
        s = PackageSerializer(data=request.data)
        if s.is_valid():
            d = s.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO package
                    (restaurant_id, package_name, price)
                    VALUES (%s,%s,%s)
                """, [d["restaurant_id"], d["package_name"], d["price"]])
            return Response({"message": "Package created"}, status=status.HTTP_201_CREATED)
        return Response(s.errors, 400)

class PackageAddFoodView(APIView):
    def post(self, request):
        s = PackageFoodSerializer(data=request.data)
        if s.is_valid():
            d = s.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO package_food
                    (package_id, food_id, quantity)
                    VALUES (%s,%s,%s)
                """, [d["package_id"], d["food_id"], d["quantity"]])
            return Response({"message": "Food added to package"}, status=status.HTTP_201_CREATED)
        return Response(s.errors, 400)

class PackageAddDrinkView(APIView):
    def post(self, request):
        s = PackageDrinkSerializer(data=request.data)
        if s.is_valid():
            d = s.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO package_drink
                    (package_id, drink_id, quantity)
                    VALUES (%s,%s,%s)
                """, [d["package_id"], d["drink_id"], d["quantity"]])
            return Response({"message": "Drink added to package"}, status=status.HTTP_201_CREATED)
        return Response(s.errors, 400)


# ===== Branch CRUD =====
class BranchCreateView(APIView):
    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                # Branch нэмэх
                c.execute("""
                    INSERT INTO tbl_res_branch ("branchName", "resID", "location", "phone")
                    VALUES (%s, %s, %s, %s)
                    RETURNING "branchID"
                """, [d['branchName'], d['resID'], d.get('location',''), d.get('phone','')])
                branch_id = c.fetchone()[0]

            return Response({"message": "Branch added", "branchID": branch_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BranchListView(APIView):
    def get(self, request):
        resID = request.query_params.get("resID")
        with connection.cursor() as c:
            if resID:
                c.execute("""
                    SELECT "branchID","branchName","resID","location","phone"
                    FROM tbl_res_branch WHERE "resID"=%s
                """, [resID])
            else:
                c.execute('SELECT "branchID","branchName","resID","location","phone" FROM tbl_res_branch')
            rows = c.fetchall()
        data = [{"branchID": r[0], "branchName": r[1], "resID": r[2], "location": r[3], "phone": r[4]} for r in rows]
        return Response(data, status=status.HTTP_200_OK)


class BranchUpdateView(APIView):
    def put(self, request, branchID):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_res_branch
                    SET "branchName"=%s, "resID"=%s, "location"=%s, "phone"=%s
                    WHERE "branchID"=%s
                """, [d['branchName'], d['resID'], d.get('location',''), d.get('phone',''), branchID])
            return Response({"message": "Branch updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BranchDeleteView(APIView):
    def delete(self, request, branchID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_res_branch WHERE "branchID"=%s', [branchID])
        return Response({"message": "Branch deleted"}, status=status.HTTP_200_OK)


# ===== Create Category =====
class RestaurantCategoryCreateView(APIView):
    def post(self, request):
        serializer = RestaurantCategorySerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute('INSERT INTO tbl_res_type ("name") VALUES (%s) RETURNING "ID"', [d['name']])
                cat_id = c.fetchone()[0]
            return Response({"message": "Category added", "id": cat_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== List Category =====
class RestaurantCategoryListView(APIView):
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "ID", "name" FROM tbl_res_type')  # double quotes-тэй
            rows = c.fetchall()
        data = [{"id": r[0], "name": r[1]} for r in rows]
        return Response(data, status=status.HTTP_200_OK)


# ===== Update Category =====
class RestaurantCategoryUpdateView(APIView):
    def put(self, request, id):
        serializer = RestaurantCategorySerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute('UPDATE tbl_res_type SET "name"=%s WHERE "ID"=%s', [d['name'], id])
            return Response({"message": "Category updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== Delete Category =====
class RestaurantCategoryDeleteView(APIView):
    def delete(self, request, id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_res_type WHERE "ID"=%s', [id])
        return Response({"message": "Category deleted"}, status=status.HTTP_200_OK)