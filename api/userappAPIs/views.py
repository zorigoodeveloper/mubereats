from datetime import datetime
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..database import execute_query, execute_insert, execute_update
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication
from .serializers import ProfileSearchSerializer, CustomerSignUpSerializer, SignInSerializer, UserSearchSerializer, CartItemSerializer, AddToCartSerializer, CartItemUpdateSerializer

# сагслах үйлдэл
# Сагс руу үйлчилгээ нэмэх
class CartView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer сагс харах боломжтой"}, status=403)

        # 1. Хэрэглэгчийн сагс олох
        cart = execute_query(
            """
            SELECT "cartID" FROM tbl_cart 
            WHERE "userID" = %s
            LIMIT 1
            """,
            (user.id,),
            fetch_one=True
        )

        if not cart:
            return Response({
                "cart": None,
                "items": [],
                "message": "Таны сагс хоосон байна"
            }, status=200)

        cart_id = cart['cartID']

        # 2. Сагсны item-үүдийг авах (foods JOIN-г түр хасав)
        items = execute_query(
            """
            SELECT 
                cf."foodID",
                cf.stock AS quantity,
                cf."foodID" AS food_name,   -- түр зуур foodId-г нэр болгож ашиглаж байна
                0 AS unit_price,            -- foods байхгүй учраас 0 эсвэл null
                0 AS subtotal               -- тооцоолохгүй
            FROM tbl_cart_food cf
            WHERE cf."cartID" = %s AND cf."userID" = %s
            ORDER BY cf."foodID"
            """,
            (cart_id, user.id)
        )

        # 3. Нийт үнэ тооцоолох (unit_price байхгүй учраас 0 болго)
        total = 0  # foods байхгүй учраас 0

        return Response({
            "cartID": cart_id,
            "total_items": len(items or []),
            "total_price": str(total),
            "items": items or [],
            "note": "foods хүснэгт байхгүй учраас нэр/үнэ харуулахгүй байна. db хариуцагчтай холбогдоорой."
        }, status=200)

class AddToCartView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer сагс ашиглаж болно"}, status=403)

        data = request.data
        food_id = data.get('foodID')
        quantity = data.get('quantity', 1)

        if not food_id or not isinstance(quantity, int) or quantity < 1:
            return Response({"error": "foodId болон зөв quantity (1-ээс их тоо) заавал шаардлагатай"}, status=400)

        # 1. Хэрэглэгчийн сагс олох
        cart = execute_query(
            """
            SELECT "cartID" FROM tbl_cart 
            WHERE "userID" = %s
            LIMIT 1
            """,
            (user.id,),
            fetch_one=True
        )

        if cart:
            cart_id = cart['cartID']
        else:
            # Шинэ cartID гар аргаар үүсгэх (bigint-д тохирох тоо)
            # timestamp-г их тоо болгож (миллисек * 1000 + random)
            import time
            import random
            new_cart_id = int(time.time() * 1000000) + random.randint(1, 999999)  # өвөрмөц байлгах

            cart = execute_insert(
                """
                INSERT INTO tbl_cart ("cartID", "userID") 
                VALUES (%s, %s) 
                RETURNING "cartID"
                """,
                (new_cart_id, user.id)
            )
            cart_id = cart['cartID']

        # 2. Энэ хоол аль хэдийн байгаа эсэх шалгах
        existing = execute_query(
            """
            SELECT "cartID", stock 
            FROM tbl_cart_food 
            WHERE "cartID" = %s AND "foodID" = %s AND "userID" = %s
            """,
            (cart_id, food_id, user.id),
            fetch_one=True
        )

        if existing:
            new_quantity = existing['stock'] + quantity
            execute_update(
                """
                UPDATE tbl_cart_food 
                SET stock = %s 
                WHERE "cartID" = %s AND "foodID" = %s AND "userID" = %s
                """,
                (new_quantity, cart_id, food_id, user.id)
            )
        else:
            execute_insert(
                """
                INSERT INTO tbl_cart_food ("cartID", "userID", "foodID", stock)
                VALUES (%s, %s, %s, %s)
                """,
                (cart_id, user.id, food_id, quantity)
            )

        return Response({
            "message": "Сагсанд амжилттай нэмэгдлээ",
            "foodId": food_id,
            "quantity_added": quantity,
            "cartID": cart_id
        }, status=201)

# Сагсны нэг item-ийг засах (quantity эсвэл note)
class CartItemUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, food_id):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer засах боломжтой"}, status=403)

        data = request.data
        new_quantity = data.get('quantity')

        if new_quantity is None or not isinstance(new_quantity, int) or new_quantity < 1:
            return Response({"error": "Шинэ тоо (quantity) 1-ээс их бүхэл тоо байх ёстой"}, status=400)

        updated = execute_update(
            """
            UPDATE tbl_cart_food 
            SET stock = %s 
            WHERE "foodId" = %s AND "userID" = %s
            """,
            (new_quantity, food_id, user.id)
        )

        if updated == 0:
            return Response({"error": "Энэ хоол таны сагсанд байхгүй"}, status=404)

        return Response({"message": "Тоо амжилттай шинэчлэгдлээ"}, status=200)
    

class CartItemDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, food_id):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer устгах боломжтой"}, status=403)

        deleted = execute_update(
            """
            DELETE FROM tbl_cart_food 
            WHERE "foodId" = %s AND "userID" = %s
            """,
            (food_id, user.id)
        )

        if deleted == 0:
            return Response({"error": "Энэ хоол таны сагсанд байхгүй"}, status=404)

        return Response({"message": "Сагснаас устгагдлаа"}, status=204)
# Dummy data
USERS = [
    {"id": 1, "username": "ebe", "location": "Ulaanbaatar"},
    {"id": 2, "username": "mori", "location": "Darkhan"},
    {"id": 3, "username": "adiya", "location": "25"},
    {"id": 4, "username": "4nottt", "location": "Erdenet"},
]

class CreateOrderView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        # Зөвхөн customer order үүсгэнэ
        if user['user_type'] != 'customer':
            return Response(
                {'error': 'Зөвхөн customer захиалга үүсгэх боломжтой'},
                status=status.HTTP_403_FORBIDDEN
            )

        location = data.get('location')
        status_value = data.get('status', 'pending')

        if not location:
            return Response(
                {'error': 'location заавал шаардлагатай'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # orderID-г автоматаар үүсгэх (timestamp ашиглан давхцахгүй бүхэл тоо үүсгэх)
        order_id = int(datetime.now().timestamp() * 1000000)

        order = execute_insert(
            """
            INSERT INTO tbl_order ("orderID", "userID", date, location, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING "orderID", "userID", date, location, status
            """,
            (
                order_id,
                str(user['id']),
                datetime.now().date(),
                location,
                status_value
            )
        )

        if not order:
            return Response(
                {'error': 'Захиалга үүсгэхэд алдаа гарлаа'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': 'Захиалга амжилттай үүслээ',
            'order': {
                'orderID': order['orderID'],
                'userID': order['userID'],
                'date': order['date'],
                'location': order['location'],
                'status': order['status']
            }
        }, status=status.HTTP_201_CREATED)

class OrderListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        orders = execute_query(
            """
            SELECT "orderID", status, date, location
            FROM tbl_order
            WHERE "userID" = %s
            ORDER BY date DESC
            """,
            (user['id'],)
        )
        
        return Response({'orders': orders or []}, status=status.HTTP_200_OK)

class UserSearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        name = request.query_params.get("name", "").lower()
        location = request.query_params.get("location", "").lower()

        results = []
        for u in USERS:
            if name and name not in u["username"].lower():
                continue
            if location and location not in u["location"].lower():
                continue
            results.append(u)

        serializer = ProfileSearchSerializer(results, many=True)
        return Response(serializer.data)


# ====== ХЭРЭГЛЭГЧЭЭР БҮРТГҮҮЛЭХ ======
class CustomerSignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerSignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        password_hash = hash_password(validated_data['password'])

        # Хэрэглэгч үүсгэх
        user = execute_insert(
            """
            INSERT INTO users (email, phone_number, password_hash, full_name, user_type)
            VALUES (%s, %s, %s, %s, 'customer')
            RETURNING id, email, phone_number, full_name, user_type, is_active, is_verified, created_at
            """,
            (
                validated_data['email'],
                validated_data['phone_number'],
                password_hash,
                validated_data['full_name']
            )
        )

        if not user:
            return Response({'error': 'Бүртгэл үүсгэхэд алдаа гарлаа'}, status=500)

        # Customer profile үүсгэх
        execute_insert(
            """
            INSERT INTO customer_profiles (user_id, default_address, latitude, longitude)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user['id'],
                validated_data.get('default_address'),
                validated_data.get('latitude'),
                validated_data.get('longitude')
            )
        )

        access_token = create_access_token(user['id'], user['email'])

        return Response({
            'message': 'Хэрэглэгчээр амжилттай бүртгэгдлээ',
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'phone_number': user['phone_number'],
                'full_name': user['full_name'],
                'user_type': 'customer',
                'is_verified': user['is_verified']
            },
            'access_token': access_token
        }, status=status.HTTP_201_CREATED)




class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (data['email'],),
            fetch_one=True
        )
        
        if not user or not verify_password(data['password'], user['password_hash']):
            return Response(
                {'error': 'Имэйл эсвэл нууц үг буруу байна'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user['is_active']:
            return Response(
                {'error': 'Таны бүртгэл идэвхгүй байна'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        access_token = create_access_token(user['id'], user['email'])
        
        return Response({
            'message': 'Амжилттай нэвтэрлээ',
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'phone_number': user['phone_number'],
                'full_name': user['full_name'],
                'user_type': user['user_type'],
                'is_verified': user['is_verified']
            },
            'access_token': access_token
        }, status=status.HTTP_200_OK)
    
# profile засах болон харах API
class ProfileUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        profile_data = None
        if user.user_type == 'driver':        
            profile_data = execute_query(
                """
                SELECT dp.*, 
                       (dp.restaurant_id IS NOT NULL AND dp.is_approved) AS is_active_driver,
                       r.name AS restaurant_name
                FROM driver_profiles dp
                LEFT JOIN restaurants r ON r.id = dp.restaurant_id
                WHERE dp.user_id = %s
                """,
                (user.id,),                     # ← user.id
                fetch_one=True
            )
        elif user.user_type == 'customer':
            profile_data = execute_query(
                "SELECT * FROM customer_profiles WHERE user_id = %s",
                (user.id,),
                fetch_one=True
            )
        
        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'phone_number': getattr(user, 'phone_number', None),
                'full_name': user.full_name,
                'user_type': user.user_type,
                'is_verified': user.is_verified,
                'profile_image_url': getattr(user, 'profile_image_url', None)
            },
            'profile': profile_data or {}
        })

    # ← ЭНДЭЭС PATCH метод нэмнэ
    def patch(self, request):
        user = request.user
        data = request.data

        if not data:
            return Response({"detail": "Засах талбар оруулаагүй байна"}, status=400)

        updated = False

        user_updates = {}
        if 'full_name' in data:
            user_updates['full_name'] = data['full_name']
            updated = True
        if 'profile_image_url' in data:
            user_updates['profile_image_url'] = data['profile_image_url']
            updated = True

        if user_updates:
            set_clause = ", ".join([f"{k} = %s" for k in user_updates])
            values = list(user_updates.values())
            values.append(str(user['id']))               # ← user['id'] болгосон

            execute_update(
                f"UPDATE users SET {set_clause} WHERE id = %s",
                tuple(values)
            )

        # Customer profile
        if user['user_type'] == 'customer':             # ← dict шиг хандана
            customer_updates = {}
            if 'default_address' in data:
                customer_updates['default_address'] = data['default_address']
            if 'latitude' in data:
                customer_updates['latitude'] = data['latitude']
            if 'longitude' in data:
                customer_updates['longitude'] = data['longitude']

            if customer_updates:
                set_clause = ", ".join([f"{k} = %s" for k in customer_updates])
                values = list(customer_updates.values())
                values.append(str(user['id']))           # ← user['id']

                execute_update(
                    f"UPDATE customer_profiles SET {set_clause} WHERE user_id = %s",
                    tuple(values)
                )
                updated = True

        # Шинэчлэгдсэн user-ийг буцаах
        updated_user = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (str(user['id']),),
            fetch_one=True
        )

        return Response({
            'message': 'Профайл амжилттай шинэчлэгдлээ' if updated else 'Өөрчлөлт хийгдээгүй',
            'user': {
                'id': str(updated_user['id']),
                'email': updated_user['email'],
                'phone_number': updated_user['phone_number'],
                'full_name': updated_user['full_name'],
                'user_type': updated_user['user_type'],
                'is_verified': updated_user['is_verified'],
                'profile_image_url': updated_user.get('profile_image_url')
            }
        }, status=status.HTTP_200_OK)

class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        profile_data = None
        if user['user_type'] == 'driver':
            profile_data = execute_query(
                """
                SELECT dp.*, 
                       (dp.restaurant_id IS NOT NULL AND dp.is_approved) AS is_active_driver,
                       r.name AS restaurant_name
                FROM driver_profiles dp
                LEFT JOIN restaurants r ON r.id = dp.restaurant_id
                WHERE dp.user_id = %s
                """,
                (user['id'],),
                fetch_one=True
            )
        elif user['user_type'] == 'customer':
            profile_data = execute_query(
                "SELECT * FROM customer_profiles WHERE user_id = %s",
                (user['id'],),
                fetch_one=True
            )
        
        return Response({
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'phone_number': user['phone_number'],
                'full_name': user['full_name'],
                'user_type': user['user_type'],
                'is_verified': user['is_verified'],
                'profile_image_url': user.get('profile_image_url')
            },
            'profile': profile_data or {}
        })