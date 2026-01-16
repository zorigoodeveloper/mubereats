import cloudinary
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import datetime, time
from cloudinary_storage.storage import MediaCloudinaryStorage
import os
from django.core.files.storage import FileSystemStorage
import uuid
import cloudinary.uploader
import time


from config import settings
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


cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)

ALLOWED_TRANSITIONS = {
    "PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PREPARING", "CANCELLED"],
    "PREPARING": ["READY"],
    "READY": ["ON_DELIVERY"],
}




# ===== Restaurant CRUD =====
class RestaurantCreateView(APIView):
    permission_classes = [AllowAny]  # public access

    def post(self, request):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data

            # ===== Validate required fields =====
            required_fields = ["resName", "catID", "phone", "email", "password", "lng", "lat", "openTime", "closeTime"]
            missing = [f for f in required_fields if not d.get(f)]
            if missing:
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            phone = str(d.get('phone')).strip()
            email = str(d.get('email')).strip()
            catID = d.get('catID')
            lng = d.get('lng')
            lat = d.get('lat')
            password_raw = d.get('password')

            # ===== Type check =====
            try:
                catID = int(catID)
                lng = float(lng)
                lat = float(lat)
            except ValueError:
                return Response(
                    {"error": "catID must be integer, lng and lat must be numeric"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ===== Check for duplicate phone/email =====
            with connection.cursor() as c:
                c.execute("""
                    SELECT "resID" FROM tbl_restaurant
                    WHERE "phone" = %s OR "email" = %s
                """, [phone, email])
                existing = c.fetchone()
                if existing:
                    return Response(
                        {"error": "Phone or Email already exists"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # ===== Hash password =====
                password_hashed = make_password(password_raw)

                # ===== Insert restaurant =====
                c.execute("""
                    INSERT INTO tbl_restaurant
                    ("resName", "catID", "phone", "password", "lng", "lat", "openTime", "closeTime", "description", "image", "email", "status")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "resID"
                """, [
                    d.get('resName',''), catID, phone, password_hashed,
                    lng, lat, d.get('openTime',''), d.get('closeTime',''),
                    d.get('description',''), d.get('image',''), email, d.get('status','active')
                ])
                res_id = c.fetchone()[0]

            return Response({"message": "Restaurant added", "resID": res_id}, status=status.HTTP_201_CREATED)

        # Serializer validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#http://127.0.0.1:8000/api/restaurant/profileres/5/
class RestaurantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, res_id):
        try:
            res_id = int(res_id)
        except ValueError:
            return Response(
                {"error": "Invalid restaurant ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as c:
            c.execute("""
                SELECT
                    r."resID",
                    r."resName",
                    r."catID",
                    r."phone",
                    r."email",
                    r."lng",
                    r."lat",
                    r."openTime",
                    r."closeTime",
                    r."description",
                    r."status",

                    -- profile зураг
                    MAX(
                        CASE
                            WHEN i."type" = 'profile' THEN i."image_url"
                        END
                    ) AS profile_image,

                    -- logo зураг
                    MAX(
                        CASE
                            WHEN i."type" = 'logo' THEN i."image_url"
                        END
                    ) AS logo_image

                FROM tbl_restaurant r
                LEFT JOIN tbl_restaurant_images i
                    ON i."resID" = r."resID"

                WHERE r."resID" = %s
                GROUP BY r."resID"
            """, [res_id])

            res = c.fetchone()

        if not res:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        keys = [
            "resID",
            "resName",
            "catID",
            "phone",
            "email",
            "lng",
            "lat",
            "openTime",
            "closeTime",
            "description",
            "status",
            "profile_image",
            "logo_image",
        ]

        res_data = dict(zip(keys, res))

        return Response({"restaurant": res_data}, status=status.HTTP_200_OK)


class RestaurantListView(APIView):
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny] # эсвэл isAuthenticated

    def delete(self, request, resID):
        with connection.cursor() as c:
            # 1️⃣ Холбоотой review-уудыг устгах
            c.execute('DELETE FROM tbl_review_rating WHERE "resID" = %s', [resID])

            # 2️⃣ Холбоотой food-уудыг устгах
            c.execute('DELETE FROM tbl_food WHERE "resID" = %s', [resID])

            # 3️⃣ Холбоотой drink-уудыг устгах
            c.execute('DELETE FROM tbl_drinks WHERE "res_id" = %s', [resID])

            # 4️⃣ Холбоотой package_food-уудыг устгах
            c.execute("""
                DELETE FROM tbl_package_food 
                WHERE package_id IN (SELECT package_id FROM tbl_package WHERE restaurant_id = %s)
            """, [resID])

            # 5️⃣ Холбоотой package_drinks-уудыг устгах
            c.execute("""
                DELETE FROM tbl_package_drinks 
                WHERE package_id IN (SELECT package_id FROM tbl_package WHERE restaurant_id = %s)
            """, [resID])

            # 6️⃣ Холбоотой package-уудыг устгах
            c.execute('DELETE FROM tbl_package WHERE restaurant_id = %s', [resID])

            # 7️⃣ Рестораныг устгах
            c.execute('DELETE FROM tbl_restaurant WHERE "resID" = %s', [resID])
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
def is_restaurant_open(open_time, close_time):
    """
    Open/Close цагийг харьцуулж, ресторан нээлттэй эсэхийг буцаана.
    None орж ирвэл хаалттай гэж үзнэ.
    Шөнө дамжих цагийг ч зөв шалгана.
    """
    if not open_time or not close_time:
        return False  # Null орж ирвэл хаалттай

    now = datetime.now().time()

    # Хэрвээ шөнө дамжих цаггүй бол энгийн шалгалт
    if open_time < close_time:
        return open_time <= now <= close_time
    else:
        # Шөнө дамжих (жишээ: 22:00 - 03:00)
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
    permission_classes = [AllowAny]

    def get(self, request, res_id):
        search = request.query_params.get('search')
        cat_id = request.query_params.get('catID')

        query = """
            SELECT 
                f."foodID", f."foodName", f."price",
                f."description", f."image",
                f."catID",
                r."resID", r."resName", r."status"
            FROM tbl_food f
            JOIN tbl_restaurant r ON f."resID" = r."resID"
            WHERE f."resID" = %s
        """
        params = [res_id]

        if cat_id:
            query += ' AND f."catID" = %s'
            params.append(int(cat_id))

        if search:
            query += ' AND (f."foodName" ILIKE %s OR f."description" ILIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])

        query += ' ORDER BY f."foodName"'

        with connection.cursor() as c:
            c.execute(query, params)
            rows = c.fetchall()

        foods = []
        for row in rows:
            foods.append({
                "foodID": row[0],
                "foodName": row[1],
                "price": float(row[2]),
                "description": row[3],
                "image": row[4],
                "catID": row[5],
                "resID": row[6],
                "resName": row[7],
                "restaurant_status": row[8],
                "image_url": request.build_absolute_uri(f"/media/{row[4]}") if row[4] else None
            })

        return Response({
            "restaurant_id": res_id,
            "count": len(foods),
            "foods": foods
        })

class FoodCreateView(APIView):
    permission_classes = [AllowAny]  # Дараа нь isAuthenticated болгож болно

    def post(self, request):
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            image_file = request.FILES.get("image")  # Frontend-с ирж байгаа файл

            image_url = ''
            if image_file:
                # Cloudinary-д upload хийх
                upload = cloudinary.uploader.upload(
                image_file,
                folder=f"foods/",
                public_id = f"{d['foodName']}",
                overwrite=True
                )
                image_url = upload["secure_url"]

            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_food ("foodName","resID","catID","price","description","image","portion")
                    VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING "foodID"
                """, [
                    d['foodName'],
                    d['resID'],
                    d['catID'],
                    d['price'],
                    d.get('description', ''),
                    image_url,  # Cloudinary URL-ийг энд хадгална
                    d.get('portion', '')
                ])
                foodID = c.fetchone()[0]

            return Response({"message": "Food added", "foodID": foodID, "image_url": image_url}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, foodID):
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_food SET "foodName"=%s,"resID"=%s,"catID"=%s,"price"=%s,"description"=%s,"image"=%s,"portion"=%s
                    WHERE "foodID"=%s
                """, [d['foodName'], d['resID'], d['catID'], d['price'], d.get('description',''), d.get('image',''), d.get('portion',''), foodID])
            return Response({"message": "Food updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodDeleteView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def delete(self, request, foodID):
        with connection.cursor() as c:
            c.execute('DELETE FROM tbl_food WHERE "foodID"=%s', [foodID])
        return Response({"message": "Food deleted"})

class FoodDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, foodID):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    f."foodID",
                    f."foodName",
                    f."price",
                    f."description",
                    f."image",
                    f."catID",
                    f."resID"
                FROM tbl_food f
                WHERE f."foodID" = %s
            """, [foodID])
            
            row = cursor.fetchone()
            if not row:
                return Response({"error": "Food not found"}, status=404)

        data = {
            "foodID": row[0],
            "foodName": row[1],
            "price": row[2],
            "description": row[3],
            "image": row[4],
            "catID": row[5],
            "resID": row[6],
        }

        return Response(data)

# ------------------- DRINK -------------------
class DrinkListView(APIView):
    permission_classes = [AllowAny]  # Дараа нь isAuthenticated болгож болно

    def get(self, request, res_id):
        search = request.query_params.get('search')

        # SQL query
        query = """
            SELECT 
                d."drink_id", d."drink_name", d."price", d."description", d."img",
                r."resID", r."resName", r."status"
            FROM tbl_drinks d
            JOIN tbl_restaurant r ON d."resID" = r."resID"
            WHERE r."resID" = %s
        """
        params = [res_id]

        # Search filter
        if search:
            query += ' AND (d."drink_name" ILIKE %s OR d."description" ILIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])

        query += ' ORDER BY d."drink_name"'

        with connection.cursor() as c:
            c.execute(query, params)
            rows = c.fetchall()

        drinks = []
        for row in rows:
            drinks.append({
                "drink_id": row[0],
                "drink_name": row[1],
                "price": float(row[2]),
                "description": row[3],
                "img": row[4],
                "resID": row[5],
                "resName": row[6],
                "restaurant_status": row[7],
                "image_url": row[4]  # Cloudinary URL
            })

        return Response({
            "restaurant_id": res_id,
            "count": len(drinks),
            "drinks": drinks
        })

class DrinkCreateView(APIView):
    permission_classes = [AllowAny]  # Дараа нь isAuthenticated болгож болно

    def post(self, request):
        serializer = DrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data

            image_file = request.FILES.get("image")  # Frontend-с ирсэн файл
            image_url = ''

            if image_file:
                upload = cloudinary.uploader.upload(
                    image_file,
                    folder="drinks/",
                    public_id=f"{d['drink_name']}",
                    overwrite=True
                )
                image_url = upload["secure_url"]

            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO tbl_drinks
                        ("drink_name", "resID", "price", "description", "img")
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING "drink_id"
                """, [
                    d['drink_name'],
                    d['resID'],        # 🔥 restaurant ID хадгалагдана
                    d['price'],
                    d.get('description', ''),
                    image_url
                ])

                drink_id = c.fetchone()[0]

            return Response({
                "message": "Drink added",
                "drink_id": drink_id,
                "image_url": image_url
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DrinkUpdateView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def put(self, request, drink_id):
        serializer = DrinkSerializer(data=request.data)
        if serializer.is_valid():
            d = serializer.validated_data
            with connection.cursor() as c:
                c.execute("""
                    UPDATE tbl_drinks SET "drink_name"=%s,"price"=%s,"description"=%s,"img"=%s WHERE "drink_id"=%s
                """, [d['drink_name'], d['price'], d.get('description',''), d.get('img',''), drink_id])
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
                    INSERT INTO tbl_package ("restaurant_id","package_name","price","portion","img")
                    VALUES (%s,%s,%s,%s,%s) RETURNING "package_id"
                """, [d['restaurant_id'], d['package_name'], d['price'],d['portion'],d['img']])
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

class RestaurantPackageListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):
        print(f"🔍 Рестораны ID: {resID}")
        
        try:
            with connection.cursor() as cursor:
                # 1. Ресторан байгаа эсэхийг шалгах (БАГИЙН ДҮРМИЙГ АШИГЛАХ)
                cursor.execute('SELECT "resID", "resName" FROM tbl_restaurant WHERE "resID" = %s', [resID])
                restaurant = cursor.fetchone()
                
                if not restaurant:
                    return Response({
                        "error": "Ресторан олдсонгүй",
                        "restaurant_id": resID
                    }, status=404)
                
                print(f"✅ Ресторан олдлоо: ID={restaurant[0]}, Name={restaurant[1]}")
                
                # 2. Багцууд байгаа эсэхийг шалгах
                cursor.execute('SELECT "package_id", "package_name" FROM tbl_package WHERE "restaurant_id" = %s', [resID])
                packages = cursor.fetchall()
                
                if not packages:
                    return Response({
                        "message": "Энэ ресторанд багц олдсонгүй",
                        "restaurant_id": resID,
                        "restaurant_name": restaurant[1]
                    })
                
                print(f"✅ {len(packages)} багц олдлоо")
                
                # 3. Бүрэн query ажиллуулах (БАГИЙН ДҮРМИЙГ АШИГЛАХ)
                cursor.execute("""
                    SELECT 
                        p."package_id",
                        p."package_name",
                        p."price",
                        p."portion",
                        p."img",
                        COALESCE(json_agg(
                            json_build_object(
                                'foodID', f."foodID",
                                'foodName', f."foodName",
                                'price', f."price",
                                'quantity', pf."quantity",
                                'subtotal', pf."quantity" * f."price",
                                'image', f."image"
                            )
                        ) FILTER (WHERE f."foodID" IS NOT NULL), '[]') AS foods
                    FROM tbl_package p
                    LEFT JOIN tbl_package_food pf ON p."package_id" = pf."package_id"
                    LEFT JOIN tbl_food f ON f."foodID" = pf."food_id"
                    WHERE p."restaurant_id" = %s
                    GROUP BY p."package_id", p."package_name", p."price", p."portion", p."img"
                    ORDER BY p."package_name"
                """, [resID])
                
                rows = cursor.fetchall()
                print(f"✅ Бүрэн query-ийн үр дүн: {len(rows)} мөр")
                
        except Exception as e:
            print(f"❌ Алдаа гарлаа: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
        
        # Өгөгдлийг бэлтгэх
        data = []
        for r in rows:
            foods = r[5] if r[5] else []
            total_price = sum(f.get('subtotal', 0) for f in foods)
            
            data.append({
                "package_id": r[0],
                "package_name": r[1],
                "price": float(r[2]) if r[2] is not None else float(total_price),
                "portion": r[3],
                "img": r[4],
                "total_price_computed": float(total_price),
                "foods": foods
            })
        
        return Response(data)

class PackageDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, packageID):
        try:
            with connection.cursor() as cursor:
                # БАГИЙН ДҮРМИЙГ АШИГЛАХ
                cursor.execute("""
                    SELECT 
                        p."package_id",
                        p."package_name",
                        p."price",
                        p."portion",
                        p."img",
                        COALESCE(json_agg(
                            json_build_object(
                                'foodID', f."foodID",
                                'foodName', f."foodName",
                                'price', f."price",
                                'quantity', pf."quantity",
                                'subtotal', pf."quantity" * f."price",
                                'image', f."image"
                            )
                        ) FILTER (WHERE f."foodID" IS NOT NULL), '[]') AS foods
                    FROM tbl_package p
                    LEFT JOIN tbl_package_food pf ON p."package_id" = pf."package_id"
                    LEFT JOIN tbl_food f ON f."foodID" = pf."food_id"
                    WHERE p."package_id" = %s
                    GROUP BY p."package_id"
                """, [packageID])
                
                row = cursor.fetchone()
                if not row:
                    return Response({"error": "Багц олдсонгүй"}, status=404)

        except Exception as e:
            print(f"❌ Алдаа гарлаа: {str(e)}")
            return Response({"error": str(e)}, status=500)

        foods = row[5] if row[5] else []
        total_price = sum(f.get('subtotal', 0) for f in foods)

        return Response({
            "package_id": row[0],
            "package_name": row[1],
            "price": float(row[2]) if row[2] is not None else float(total_price),
            "portion": row[3],
            "img": row[4],
            "total_price_computed": float(total_price),
            "foods": foods
        })


# ------------------- PACKAGE FOOD -------------------
class PackageFoodListView(APIView):
    permission_classes = [AllowAny] #test hiij duusni ardaas [isAuthenticated bolgn]
    def get(self, request):
        with connection.cursor() as c:
            c.execute('SELECT "id","package_id","food_id","quantity","portion","img" FROM tbl_package_food')
            rows = c.fetchall()
        data = [{"id": r[0], "package_id": r[1], "food_id": r[2], "quantity": r[3],"portion": r[4],"img": r[5] }   for r in rows]
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

class RestaurantPackageFoodListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):
        with connection.cursor() as c:
            c.execute(
                '''
                SELECT 
                    pf."id",
                    pf."package_id",
                    pf."food_id",
                    pf."quantity"
                FROM tbl_package_food pf
                JOIN tbl_package p 
                    ON p."package_id" = pf."package_id"
                WHERE p."restaurant_id" = %s
                ''',
                [resID]
            )
            rows = c.fetchall()

        data = [
            {
                "id": r[0],
                "package_id": r[1],
                "food_id": r[2],
                "quantity": r[3]
            }
            for r in rows
        ]

        return Response(data)


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

class RestaurantPackageDrinkListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):   # 👈 resID
        with connection.cursor() as c:
            c.execute(
                '''
                SELECT 
                    pd."id",
                    pd."package_id",
                    pd."drink_id",
                    pd."quantity"
                FROM tbl_package_drinks pd
                JOIN tbl_package p
                    ON p."package_id" = pd."package_id"
                WHERE p."restaurant_id" = %s
                ''',
                [resID]   # 👈 resID
            )
            rows = c.fetchall()

        data = [
            {
                "id": r[0],
                "package_id": r[1],
                "drink_id": r[2],
                "quantity": r[3]
            }
            for r in rows
        ]

        return Response(data)


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
    
class ImageUploadView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # 1. Зураг файл шалгах
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # 2. Файлын төрөл шалгах
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid image type. Allowed: JPEG, PNG, GIF, WebP"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Файлын хэмжээ шалгах (2MB хүртэл)
        max_size = 2 * 1024 * 1024  # 2MB
        if image_file.size > max_size:
            return Response(
                {"error": "Image size too large. Max 2MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Хадгалах зам бэлдэх
        upload_dir = 'restaurant_images'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 5. Файлын нэр өвөрмөц болгох
        import uuid
        file_name = f"{uuid.uuid4()}_{image_file.name}"
        file_path = os.path.join(upload_dir, file_name)
        
        # 6. Файл хадгалах
        fs = FileSystemStorage()
        filename = fs.save(file_path, image_file)
        
        # 7. URL үүсгэх
        file_url = fs.url(filename)
        
        return Response({
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": file_url,
            "size": image_file.size,
            "content_type": image_file.content_type
        }, status=status.HTTP_201_CREATED)

class RestaurantMultipleImageUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, resID):
        files = request.FILES.getlist("images")
        if not files:
            return Response({"error": "No image files"}, status=400)

        # type: profile | logo
        file_type = request.data.get("type", "profile")
        if file_type not in ["profile", "logo"]:
            return Response({"error": "Invalid type"}, status=400)

        storage = MediaCloudinaryStorage()
        uploaded = []

        allowed_types = ["image/jpeg", "image/png", "image/webp"]

        for image_file in files[:1]:  # 🔴 1 л зураг авна
            if image_file.content_type not in allowed_types:
                return Response({"error": "Invalid image type"}, status=400)

            if image_file.size > 5 * 1024 * 1024:
                return Response({"error": "Image too large"}, status=400)

            with connection.cursor() as c:
                # 👉 өмнө нь энэ type-тэй зураг байгаа эсэх
                c.execute("""
                    SELECT "imageID", "image_url"
                    FROM tbl_restaurant_images
                    WHERE "resID"=%s AND "type"=%s
                """, [resID, file_type])

                existing = c.fetchone()

            # Cloudinary path (overwrite хийхэд тогтмол нэр ашиглана)
            file_path = f"restaurants/{resID}/{file_type}"

            saved_name = storage.save(file_path, image_file)
            image_url = storage.url(saved_name)

            with connection.cursor() as c:
                if existing:
                    # 🔁 UPDATE
                    c.execute("""
                        UPDATE tbl_restaurant_images
                        SET "image_url"=%s
                        WHERE "imageID"=%s
                        RETURNING "imageID"
                    """, [image_url, existing[0]])
                    image_id = c.fetchone()[0]
                else:
                    # ➕ INSERT
                    c.execute("""
                        INSERT INTO tbl_restaurant_images ("resID", "image_url", "type")
                        VALUES (%s,%s,%s)
                        RETURNING "imageID"
                    """, [resID, image_url, file_type])
                    image_id = c.fetchone()[0]

            uploaded.append({
                "imageID": image_id,
                "image_url": image_url,
                "type": file_type
            })

        return Response({
            "message": "Image saved",
            "uploaded": uploaded
        }, status=200)

class RestaurantImageUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, resID):
        if 'image' not in request.FILES:
            return Response({"error": "No image file"}, status=400)

        image_file = request.FILES['image']

        # validation
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response({"error": "Invalid image type"}, status=400)

        if image_file.size > 5 * 1024 * 1024:
            return Response({"error": "Max 5MB"}, status=400)

        # 🔥 使用 Cloudinary Storage 上传
        storage = MediaCloudinaryStorage()
        
        # 构建文件路径
        file_name = f"restaurant_{resID}"
        file_path = f"restaurants/{resID}/{file_name}"
        
        # 保存文件
        file_name = storage.save(file_path, image_file)
        image_url = storage.url(file_name)

        # DB update (URL хадгална)
        with connection.cursor() as c:
            c.execute("""
                UPDATE tbl_restaurant
                SET "image" = %s
                WHERE "resID" = %s
                RETURNING "resID", "resName"
            """, [image_url, resID])

            result = c.fetchone()
            if not result:
                return Response({"error": "Restaurant not found"}, status=404)

        return Response({
            "message": "Restaurant image updated",
            "resID": result[0],
            "resName": result[1],
            "image_url": image_url
        }, status=200)

class RestaurantImageView(APIView):
    """Рестораны зураг авах (GET method нэмэх)"""

    permission_classes = [AllowAny]

    def post(self, request, resID):
        if 'image' not in request.FILES:
            return Response({"error": "No image file"}, status=400)

        image_file = request.FILES['image']

        # validation
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response({"error": "Invalid image type"}, status=400)

        if image_file.size > 5 * 1024 * 1024:
            return Response({"error": "Max 5MB"}, status=400)

        # 🔥 使用 Cloudinary Storage 上传
        storage = MediaCloudinaryStorage()
        
        # 构建文件路径
        file_name = f"logo_{resID}"
        file_path = f"restaurants/logo/{resID}/{file_name}"
        
        # 保存文件
        file_name = storage.save(file_path, image_file)
        image_url = storage.url(file_name)

        # DB update (URL хадгална)
        with connection.cursor() as c:
            c.execute("""
                UPDATE tbl_restaurant
                SET "image" = %s
                WHERE "resID" = %s
                RETURNING "resID", "resName"
            """, [image_url, resID])

            result = c.fetchone()
            if not result:
                return Response({"error": "Restaurant not found"}, status=404)

        return Response({
            "message": "Restaurant image updated",
            "resID": result[0],
            "resName": result[1],
            "image_url": image_url
        }, status=200)

class RestaurantImagesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):
        with connection.cursor() as c:
            c.execute("""
                SELECT "imageID", "image_url", "type", "created_at"
                FROM tbl_restaurant_images
                WHERE "resID" = %s
            """, [resID])
            rows = c.fetchall()

        images = [{"imageID": r[0], "image_url": r[1], "type": r[2], "created_at": r[3]} for r in rows]

        return Response({"resID": resID, "images": images})

class FoodImageUpdateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, foodID):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "No image"}, status=400)

        upload = cloudinary.uploader.upload(
            image_file,
            folder=f"foods/{foodID}",
            public_id=f"food_{foodID}",
            overwrite=True
        )

        image_url = upload["secure_url"]

        with connection.cursor() as c:
            c.execute("""
                UPDATE tbl_food
                SET "image" = %s
                WHERE "foodID" = %s
                RETURNING "foodID", "foodName", "resID"
            """, [image_url, foodID])

            result = c.fetchone()
            if not result:
                return Response({"error": "Food not found"}, status=404)

        return Response({
            "message": "Food image updated",
            "image_url": image_url
        }, status=200)
    

class RestaurantOrderListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    o."orderID",
                    o."status",
                    o."created_at",
                    SUM(of."stock" * of."price") AS total_price,
                    json_agg(
                        json_build_object(
                            'foodID', f."foodID",
                            'foodName', f."foodName",
                            'stock', of."stock",
                            'price', of."price",
                            'subtotal', of."stock" * of."price"
                        )
                    ) AS foods
                FROM tbl_order o
                JOIN tbl_orderfood of ON o."orderID" = of."orderID"
                JOIN tbl_food f ON f."foodID" = of."foodID"
                WHERE f."resID" = %s
                GROUP BY o."orderID"
                ORDER BY o."created_at" DESC
            """, [resID])

            rows = cursor.fetchall()

        data = [{
            "orderID": r[0],
            "status": r[1],
            "created_at": r[2].isoformat(),
            "total_price": r[3],
            "foods": r[4]
        } for r in rows]

        return Response(data) 

class RestaurantOrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID, orderID):
        with connection.cursor() as cursor:
            # 🔐 owner check
            cursor.execute("""
                SELECT 1
                FROM tbl_order o
                JOIN tbl_orderfood of ON o."orderID" = of."orderID"
                JOIN tbl_food f ON f."foodID" = of."foodID"
                WHERE o."orderID" = %s AND f."resID" = %s
                LIMIT 1
            """, [orderID, resID])

            if not cursor.fetchone():
                return Response(
                    {"error": "Forbidden"},
                    status=status.HTTP_403_FORBIDDEN
                )

            cursor.execute("""
                SELECT
                    o."orderID",
                    o."status",
                    o."location",
                    o."created_at",
                    json_agg(
                        json_build_object(
                            'foodID', f."foodID",
                            'foodName', f."foodName",
                            'stock', of."stock",
                            'price', of."price",
                            'subtotal', of."stock" * of."price"
                        )
                    ) AS foods
                FROM tbl_order o
                JOIN tbl_orderfood of ON o."orderID" = of."orderID"
                JOIN tbl_food f ON f."foodID" = of."foodID"
                WHERE o."orderID" = %s
                GROUP BY o."orderID"
            """, [orderID])

            row = cursor.fetchone()

        return Response({
            "orderID": row[0],
            "status": row[1],
            "location": row[2],
            "created_at": row[3].isoformat(),
            "foods": row[4]
        })

class OrderStatusUpdateView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, resID, orderID):
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        with connection.cursor() as cursor:
            # 🔐 Owner check
            cursor.execute("""
                SELECT o."status"
                FROM tbl_order o
                JOIN tbl_orderfood of ON o."orderID" = of."orderID"
                JOIN tbl_food f ON f."foodID" = of."foodID"
                WHERE o."orderID" = %s AND f."resID" = %s
                LIMIT 1
            """, [orderID, resID])

            row = cursor.fetchone()
            if not row:
                return Response({"error": "Forbidden"}, status=403)

            current_status = row[0]

            # 🧠 Status validation
            if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
                return Response({"error": f"Invalid transition from {current_status} to {new_status}"}, status=400)

            # ✅ Atomic update + history
            try:
                cursor.execute("BEGIN;")

                # Update order status
                cursor.execute("""
                    UPDATE tbl_order
                    SET status = %s
                    WHERE "orderID" = %s
                """, [new_status, orderID])

                # Insert into history
                cursor.execute("""
                    INSERT INTO tbl_order_status_history ("orderID", "old_status", "new_status", "changed_at")
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """, [orderID, current_status, new_status])

                cursor.execute("COMMIT;")
            except Exception as e:
                cursor.execute("ROLLBACK;")
                return Response({"error": str(e)}, status=500)

        # 🔔 Optional: notification
        # notify_user(orderID, new_status)

        return Response({
            "message": f"Order status updated from {current_status} to {new_status}",
            "orderID": orderID,
            "new_status": new_status
        })

class NewOrderCountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, resID):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(DISTINCT o."orderID")
                FROM tbl_order o
                JOIN tbl_orderfood of ON o."orderID" = of."orderID"
                JOIN tbl_food f ON f."foodID" = of."foodID"
                WHERE f."resID" = %s
                  AND o."status" = 'PENDING'
            """, [resID])

            count = cursor.fetchone()[0]

        return Response({"new_orders": count})
