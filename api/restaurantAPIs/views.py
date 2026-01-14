from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from .serializers import (
    RestaurantSerializer,
    FoodSerializer, 
    DrinkSerializer,
    PackageSerializer, 
    PackageFoodSerializer, 
    PackageDrinkSerializer,
    RestaurantCategorySerializer,
    RestaurantSigninSerializer,
    # RestaurantSerializer,
    # PackageFoodCreateView,
    FoodSerializer,
    DrinkSerializer,
    PackageSerializer,
    PackageFoodSerializer,
    PackageDrinkSerializer,
    # PackageAddFoodView,
    # PackageAddDrinkView,  
    FoodCategorySerializer, 
    DrinkSerializer,
    PackageSerializer,
    PackageFoodSerializer,
    PackageDrinkSerializer
)
from datetime import datetime, time
import pytz
from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password





# ===== Restaurant CRUD =====
class RestaurantCreateView(APIView):
    permission_classes = [AllowAny]  # public access

    def post(self, request):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            # hash password
            password = make_password(d.get('password', ''))

            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_restaurant
                    ("resName", "catID", "phone", "password", "lng", "lat", "openTime", "closeTime", "description", "image", "email", "status")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "resID"
                """, [
                    d.get('resName',''), d.get('catID',''), d.get('phone',''), password,
                    d.get('lng',''), d.get('lat',''), d.get('openTime',''), d.get('closeTime',''),
                    d.get('description',''), d.get('image',''), d.get('email',''), d.get('status','active')
                ])
                res_id = c.fetchone()[0]

            return Response({"message": "Restaurant added", "resID": res_id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    """
    Бүх ресторануудыг жагсаана.
    openNow flag ашиглан одоогийн цагт нээлттэй эсэхийг харуулна.
    status='inactive' бол автоматаар хаалттай гэж үзнэ.
    """
    def get(self, request):
        with connection.cursor() as c:
            c.execute("""
                SELECT "resID", "resName", "catID", "phone", "lng", "lat", "openTime", "closeTime",
                       "description", "image", "email", "status"
                FROM tbl_restaurant
            """)
            rows = c.fetchall()

        data = []
        for r in rows:
            resID, resName, catID, phone, lng, lat, openTime, closeTime, description, image, email, status_val = r

            # openNow flag
            open_now = is_restaurant_open(openTime, closeTime) and status_val == 'active'

            data.append({
                "resID": resID,
                "resName": resName,
                "catID": catID,
                "phone": phone,
                "lng": lng,
                "lat": lat,
                "openTime": openTime,
                "closeTime": closeTime,
                "description": description,
                "image": image,
                "email": email,
                "status": status_val,
                "openNow": open_now
            })

        return Response(data)

class RestaurantUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, resID):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_restaurant
                    SET "resName"=%s, "catID"=%s, "phone"=%s, "password"=%s, "lng"=%s, "lat"=%s, "openTime"=%s, "closeTime"=%s, "description"=%s, "image"=%s, "email"=%s
                    WHERE "resID"=%s
                """, [d['resName'], d['catID'], d.get('phone',''), d.get('password',''), d.get('lng',''), d.get('lat',''), d.get('openTime',''), d.get('closeTime',''), d.get('description',''), d.get('image',''), d.get('email',''), resID])
            return Response({"message": "Restaurant updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, resID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_restaurant WHERE "resID"=%s', [resID])
        return Response({"message": "Restaurant deleted"}, status=status.HTTP_200_OK)


# ----------------------------
# Signin API
# ----------------------------
class RestaurantSigninView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        with connection.cursor() as c:
            c.execute("""
                SELECT "resID", "resName", "password", "status"
                FROM tbl_restaurant
                WHERE "email" = %s
            """, [email])
            res = c.fetchone()

        if not res:
            return Response({"error": "Invalid email or password"}, status=401)

        resID, resName, hashed_password, status_val = res

        from django.contrib.auth.hashers import check_password
        if not check_password(password, hashed_password):
            return Response({"error": "Invalid email or password"}, status=401)

        if status_val != 'active':
            return Response({"error": "Restaurant is inactive"}, status=403)

        # Simple token replacement: resID + email
        custom_token = f"{resID}-{email}"

        return Response({
            "message": "Login successful",
            "resID": resID,
            "resName": resName,
            "token": custom_token
        }, status=200)


# ----------------------------
# Serializer for status update
# ----------------------------
class RestaurantStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['active', 'inactive'])


# ----------------------------
# Function to check if restaurant is open (Ulaanbaatar timezone)
# ----------------------------
def is_restaurant_open(open_time: time, close_time: time) -> bool:
    tz = pytz.timezone('Asia/Ulaanbaatar')
    now = datetime.now(tz).time()

    if open_time < close_time:
        # Энгийн өдөр дундын цаг (09:00 - 21:00)
        return open_time <= now <= close_time
    else:
        # Overnight цаг (22:00 - 05:00)
        return now >= open_time or now <= close_time


# ----------------------------
# Status update API (PATCH)
# ----------------------------
class RestaurantStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # зөвхөн бүртгэлтэй хэрэглэгч

    def patch(self, request, resID):
        serializer = RestaurantStatusSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']

            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_restaurant
                    SET status = %s
                    WHERE "resID" = %s
                    RETURNING "resID"
                """, [new_status, resID])
                updated = c.fetchone()

            if not updated:
                return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": f"Restaurant status updated to {new_status}"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------
# Check restaurant status + openNow API (GET)
# ----------------------------
class RestaurantStatusCheckView(APIView):
    permission_classes = [AllowAny]  # бүгдэд нээлттэй

    def get(self, request, resID):
        with connection.cursor() as c:
            c.execute("""
                SELECT "resName", "status", "openTime", "closeTime"
                FROM tbl_restaurant
                WHERE "resID" = %s
            """, [resID])
            res = c.fetchone()

        if not res:
            return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

        res_name, status_val, open_time, close_time = res
        open_now = is_restaurant_open(open_time, close_time) and status_val == 'active'

        return Response({
            "resID": resID,
            "resName": res_name,
            "status": status_val,
            "openNow": open_now
        }, status=status.HTTP_200_OK)


# ------------------- FOOD CATEGORY -------------------
class FoodCategoryListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "catID", "catName" FROM tbl_foodtype')
            rows = c.fetchall()
        data = [{"catID": r[0], "catName": r[1]} for r in rows]
        return Response(data)

class FoodCategoryCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = FoodCategorySerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute('INSERT INTO tbl_foodtype ("catName") VALUES (%s) RETURNING "catID"', [d['catName']])
                catID = c.fetchone()[0]
            return Response({"message": "Category added", "catID": catID}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodCategoryUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, catID):
        serializer = FoodCategorySerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute('UPDATE tbl_foodtype SET "catName"=%s WHERE "catID"=%s', [d['catName'], catID])
            return Response({"message": "Category updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodCategoryDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, catID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_foodtype WHERE "catID"=%s', [catID])
        return Response({"message": "Category deleted"})


# ------------------- FOOD -------------------
class FoodListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "foodID","foodName","resID","catID","price","description","image" FROM tbl_food')
            rows = c.fetchall()
        data = [{"foodID": r[0], "foodName": r[1], "resID": r[2], "catID": r[3], "price": r[4], "description": r[5], "image": r[6]} for r in rows]
        return Response(data)

class FoodCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_food ("foodName","resID","catID","price","description","image","portion")
                    VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING "foodID"
                """, [d['foodName'], d['resID'], d['catID'], d['price'], d.get('description',''), d.get('image',''), d.get('portion','')])
                foodID = c.fetchone()[0]
            return Response({"message": "Food added", "foodID": foodID}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, foodID):
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_food SET "foodName"=%s,"resID"=%s,"catID"=%s,"price"=%s,"description"=%s,"image"=%s
                    WHERE "foodID"=%s
                """, [d['foodName'], d['resID'], d['catID'], d['price'], d.get('description',''), d.get('image',''), foodID])
            return Response({"message": "Food updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, foodID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_food WHERE "foodID"=%s', [foodID])
        return Response({"message": "Food deleted"})


# ------------------- DRINK -------------------
class DrinkListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "drink_id","drink_name","price","description" FROM tbl_drinks')
            rows = c.fetchall()
        data = [{"drink_id": r[0], "drink_name": r[1], "price": r[2], "description": r[3]} for r in rows]
        return Response(data)

class DrinkCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = DrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_drinks ("drink_name","price","description")
                    VALUES (%s,%s,%s) RETURNING "drink_id"
                """, [d['drink_name'], d['price'], d.get('description','')])
                drink_id = c.fetchone()[0]
            return Response({"message": "Drink added", "drink_id": drink_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DrinkUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, drink_id):
        serializer = DrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_drinks SET "drink_name"=%s,"price"=%s,"description"=%s WHERE "drink_id"=%s
                """, [d['drink_name'], d['price'], d.get('description',''), drink_id])
            return Response({"message": "Drink updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DrinkDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, drink_id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_drinks WHERE "drink_id"=%s', [drink_id])
        return Response({"message": "Drink deleted"})


# ------------------- PACKAGE -------------------
class PackageListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "package_id","restaurant_id","package_name","price" FROM tbl_package')
            rows = c.fetchall()
        data = [{"package_id": r[0], "restaurant_id": r[1], "package_name": r[2], "price": r[3]} for r in rows]
        return Response(data)

class PackageCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = PackageSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_package ("restaurant_id","package_name","price")
                    VALUES (%s,%s,%s) RETURNING "package_id"
                """, [d['restaurant_id'], d['package_name'], d['price']])
                package_id = c.fetchone()[0]
            return Response({"message": "Package added", "package_id": package_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, package_id):
        serializer = PackageSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_package SET "restaurant_id"=%s,"package_name"=%s,"price"=%s WHERE "package_id"=%s
                """, [d['restaurant_id'], d['package_name'], d['price'], package_id])
            return Response({"message": "Package updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, package_id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_package WHERE "package_id"=%s', [package_id])
        return Response({"message": "Package deleted"})


# ------------------- PACKAGE FOOD -------------------
class PackageFoodListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "id","package_id","food_id","quantity" FROM tbl_package_food')
            rows = c.fetchall()
        data = [{"id": r[0], "package_id": r[1], "food_id": r[2], "quantity": r[3]} for r in rows]
        return Response(data)

class PackageFoodCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = PackageFoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_package_food ("package_id","food_id","quantity")
                    VALUES (%s,%s,%s) RETURNING "id"
                """, [d['package_id'], d['food_id'], d['quantity']])
                id = c.fetchone()[0]
            return Response({"message": "Package Food added", "id": id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageFoodUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, id):
        serializer = PackageFoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_package_food SET "package_id"=%s,"food_id"=%s,"quantity"=%s WHERE "id"=%s
                """, [d['package_id'], d['food_id'], d['quantity'], id])
            return Response({"message": "Package Food updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageFoodDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_package_food WHERE "id"=%s', [id])
        return Response({"message": "Package Food deleted"})


# ------------------- PACKAGE DRINK -------------------
class PackageDrinkListView(APIView):    
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "id","package_id","drink_id","quantity" FROM tbl_package_drinks')
            rows = c.fetchall()
        data = [{"id": r[0], "package_id": r[1], "drink_id": r[2], "quantity": r[3]} for r in rows]
        return Response(data)

class PackageDrinkCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def post(self, request):
        serializer = PackageDrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_package_drinks ("package_id","drink_id","quantity")
                    VALUES (%s,%s,%s) RETURNING "id"
                """, [d['package_id'], d['drink_id'], d['quantity']])
                id = c.fetchone()[0]
            return Response({"message": "Package Drink added", "id": id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageDrinkUpdateView(APIView): 
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, id):
        serializer = PackageDrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_package_drinks SET "package_id"=%s,"drink_id"=%s,"quantity"=%s WHERE "id"=%s
                """, [d['package_id'], d['drink_id'], d['quantity'], id])
            return Response({"message": "Package Drink updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PackageDrinkDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_package_drinks WHERE "id"=%s', [id])
        return Response({"message": "Package Drink deleted"})

# # ===== Branch CRUD =====
# class BranchCreateView(APIView):
#     def post(self, request):
#         serializer = BranchSerializer(data=request.data)
#         if serializer.is_valid():
#             d = serializer.validated_data
#             with connection.cursor() as c:
#                 # Branch нэмэх
#                 c.execute("""
#                     INSERT INTO tbl_res_branch ("branchName", "resID", "location", "phone")
#                     VALUES (%s, %s, %s, %s)
#                     RETURNING "branchID"
#                 """, [d['branchName'], d['resID'], d.get('location',''), d.get('phone','')])
#                 branch_id = c.fetchone()[0]

#             return Response({"message": "Branch added", "branchID": branch_id}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class BranchListView(APIView):
#     def get(self, request):
#         resID = request.query_params.get("resID")
#         with connection.cursor() as c:
#             if resID:
#                 c.execute("""
#                     SELECT "branchID","branchName","resID","location","phone"
#                     FROM tbl_res_branch WHERE "resID"=%s
#                 """, [resID])
#             else:
#                 c.execute('SELECT "branchID","branchName","resID","location","phone" FROM tbl_res_branch')
#             rows = c.fetchall()
#         data = [{"branchID": r[0], "branchName": r[1], "resID": r[2], "location": r[3], "phone": r[4]} for r in rows]
#         return Response(data, status=status.HTTP_200_OK)


# class BranchUpdateView(APIView):
#     def put(self, request, branchID):
#         serializer = BranchSerializer(data=request.data)
#         if serializer.is_valid():
#             d = serializer.validated_data
#             with connection.cursor() as c:
#                 c.execute("""
#                     UPDATE tbl_res_branch
#                     SET "branchName"=%s, "resID"=%s, "location"=%s, "phone"=%s
#                     WHERE "branchID"=%s
#                 """, [d['branchName'], d['resID'], d.get('location',''), d.get('phone',''), branchID])
#             return Response({"message": "Branch updated"}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class BranchDeleteView(APIView):
#     def delete(self, request, branchID):
#         with connection.cursor() as c:
#             c.execute('DELETE FROM tbl_res_branch WHERE "branchID"=%s', [branchID])
#         return Response({"message": "Branch deleted"}, status=status.HTTP_200_OK)


# ===== Create Category =====
class RestaurantCategoryCreateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
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
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "ID", "name" FROM tbl_res_type')  # double quotes-тэй
            rows = c.fetchall()
        data = [{"id": r[0], "name": r[1]} for r in rows]
        return Response(data, status=status.HTTP_200_OK)


# ===== Update Category =====
class RestaurantCategoryUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
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
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, id):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_res_type WHERE "ID"=%s', [id])
        return Response({"message": "Category deleted"}, status=status.HTTP_200_OK)