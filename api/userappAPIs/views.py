from datetime import datetime
import random, time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..database import execute_query, execute_insert, execute_update
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication
from .serializers import ProfileSearchSerializer, CustomerSignUpSerializer, SignInSerializer, UserSearchSerializer

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
        try:
            user = request.user
            data = request.data

            # Зөвхөн customer order үүсгэнэ
            if user['user_type'] != 'customer':
                return Response(
                    {'error': 'Зөвхөн үйлчлүүлэгч захиалга үүсгэх боломжтой'},
                    status=status.HTTP_403_FORBIDDEN
                )

            location = data.get('location')
            status_value = data.get('status', 'pending')

            if not location:
                return Response(
                    {'error': 'location заавал шаардлагатай'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Захиалгын хоолнуудыг урьдчилан шалгах
            items = data.get('items', [])
            if not items:
                return Response({'error': 'Захиалгад хоол сонгоогүй байна'}, status=status.HTTP_400_BAD_REQUEST)

            for item in items:
                food_id = item.get('foodID')
                # Хоол баазад байгаа эсэхийг шалгах
                food_exists = execute_query('SELECT 1 FROM tbl_food WHERE "foodID" = %s', (food_id,), fetch_one=True)
                if not food_exists:
                    return Response(
                        {'error': f'Таны сонгосон хоол дууссан байна.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # orderID-г автоматаар үүсгэх (timestamp ашиглан давхцахгүй бүхэл тоо үүсгэх)
            order_id = int(datetime.now().timestamp())

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

            # Захиалгын хоолнуудыг бүртгэх
            for item in items:
                # ID-г гараар үүсгэх (random ашиглан)
                item_id = random.randint(1, 2147483647)
                execute_insert(
                    """
                    INSERT INTO tbl_orderfood ("ID", "orderID", "foodID", stock, price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        item_id,
                        order['orderID'],
                        item.get('foodID'),
                        item.get('stock'),
                        item.get('price')
                    )
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
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data['password']

        # Имэйл эсвэл phone_number-оор хайх
        if email:
            user = execute_query(
                "SELECT * FROM users WHERE email = %s",
                (email,),
                fetch_one=True
            )
        else:
            user = execute_query(
                "SELECT * FROM users WHERE phone_number = %s",
                (phone_number,),
                fetch_one=True
            )
        
        if not user or not verify_password(password, user['password_hash']):
            return Response(
                {'error': 'Имэйл/утасны дугаар эсвэл нууц үг буруу байна'},
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
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        data = request.data

        if not data:
            return Response({"detail": "Өөрчлөх талбар оруулаагүй байна"}, status=400)

        updated = False

        # 1. users хүснэгтэд нийтлэг талбарууд засах
        user_updates = {}
        
        # Full name
        if 'full_name' in data:
            user_updates['full_name'] = data['full_name'].strip()
            updated = True
        
        # Profile image
        if 'profile_image_url' in data:
            user_updates['profile_image_url'] = data['profile_image_url'].strip()
            updated = True
        
        # Phone number (давхардсан шалгалттай)
        if 'phone_number' in data:
            new_phone = data['phone_number'].strip()
            if new_phone == user['phone_number']:
                return Response({"error": "Одоогийн утасны дугаартай ижил байна"}, status=400)
            
            existing = execute_query(
                "SELECT id FROM users WHERE phone_number = %s AND id != %s",
                (new_phone, user['id']),
                fetch_one=True
            )
            if existing:
                return Response({"error": "Энэ утасны дугаар аль хэдийн бүртгэлтэй байна"}, status=400)
            
            user_updates['phone_number'] = new_phone
            updated = True
        
        # Email (давхардсан шалгалттай)
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email == user['email']:
                return Response({"error": "Одоогийн имэйлтэй ижил байна"}, status=400)
            
            existing = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (new_email, user['id']),
                fetch_one=True
            )
            if existing:
                return Response({"error": "Энэ имэйл аль хэдийн бүртгэлтэй байна"}, status=400)
            
            user_updates['email'] = new_email
            updated = True

        # users хүснэгтийг шинэчлэх
        if user_updates:
            set_clause = ", ".join([f"{k} = %s" for k in user_updates])
            values = list(user_updates.values())
            values.append(str(user['id']))

            execute_update(
                f"UPDATE users SET {set_clause} WHERE id = %s",
                tuple(values)
            )

        # 2. Customer профайл засах
        if user['user_type'] == 'customer':
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
                values.append(str(user['id']))

                execute_update(
                    f"UPDATE customer_profiles SET {set_clause} WHERE user_id = %s",
                    tuple(values)
                )
                updated = True

        # Шинэчлэгдсэн мэдээллийг буцааж харуулах
        updated_user = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (str(user['id']),),
            fetch_one=True
        )

        profile_data = None
        if updated_user['user_type'] == 'driver':
            profile_data = execute_query(
                """
                SELECT dp.*, 
                       (dp.restaurant_id IS NOT NULL AND dp.is_approved) AS is_active_driver,
                       r.name AS restaurant_name
                FROM driver_profiles dp
                LEFT JOIN restaurants r ON r.id = dp.restaurant_id
                WHERE dp.user_id = %s
                """,
                (updated_user['id'],),
                fetch_one=True
            )
        elif updated_user['user_type'] == 'customer':
            profile_data = execute_query(
                "SELECT * FROM customer_profiles WHERE user_id = %s",
                (updated_user['id'],),
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
            },
            'profile': profile_data or {}
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
    
class AddToCartView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer сагс ашиглаж болно"}, status=403)

        data = request.data
        food_id = data.get('foodID')  # эсвэл 'foodId' гэж байвал тааруул

        # Quantity-г шалгах (байхгүй эсвэл буруу бол 1 гэж тооцно)
        quantity_raw = data.get('quantity', 1)
        try:
            quantity = int(quantity_raw)
            if quantity < 1:
                quantity = 1  # 0 эсвэл сөрөг байсан ч 1 болгоно
        except (ValueError, TypeError):
            quantity = 1  # string эсвэл буруу утга байсан ч 1 гэж тооцно

        if not food_id:
            return Response({"error": "foodID (эсвэл foodId) заавал оруулна уу"}, status=400)

        # 1. Хэрэглэгчийн сагс олох эсвэл шинээр үүсгэх
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
            # Шинэ cartID (bigint-д тохирох өвөрмөц тоо)
            new_cart_id = int(time.time() * 1000000) + random.randint(1, 999999)

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
            # Байвал тоог нэмэх
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
            # Шинээр нэмэх (quantity 1 эсвэл илгээсэн утгаараа)
            execute_insert(
                """
                INSERT INTO tbl_cart_food ("cartID", "userID", "foodID", stock)
                VALUES (%s, %s, %s, %s)
                """,
                (cart_id, user.id, food_id, quantity)
            )

        return Response({
            "message": f"Сагсанд амжилттай нэмэгдлээ ({quantity} ширхэг)",
            "foodId": food_id,
            "quantity_added": quantity,
            "cartID": cart_id
        }, status=201)
    
class CartView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer сагс харах боломжтой"}, status=403)

        # Сагс олох
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

        # tbl_food хүснэгттэй холбож байна (foodName-г давхар ишлэлтэй бичсэн)
        items = execute_query(
            """
            SELECT 
                cf."foodID" AS food_id,
                cf.stock AS quantity,
                f."foodName" AS food_name,    
                f.price AS unit_price,
                (cf.stock * f.price) AS subtotal
            FROM tbl_cart_food cf
            LEFT JOIN tbl_food f ON f."foodID" = cf."foodID"
            WHERE cf."cartID" = %s AND cf."userID" = %s
            ORDER BY cf."foodID"
            """,
            (cart_id, user.id)
        )

        # Нийт үнэ тооцоолох
        total = sum(float(item['subtotal']) for item in items or [])

        return Response({
            "cartID": cart_id,
            "total_items": len(items or []),
            "total_price": str(total),
            "items": items or []
        }, status=200)
class CartItemUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, cart_item_id): 
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer засах боломжтой"}, status=403)

        data = request.data
        new_quantity = data.get('quantity')

        # quantity-г int болгох
        try:
            new_quantity = int(new_quantity)
        except (ValueError, TypeError):
            return Response({"error": "quantity нь бүхэл тоо байх ёстой"}, status=400)

        if new_quantity is None or new_quantity < 1:
            return Response({"error": "Шинэ тоо (quantity) 1-ээс их бүхэл тоо байх ёстой"}, status=400)

        updated = execute_update(
            """
            UPDATE tbl_cart_food 
            SET stock = %s 
            WHERE "foodID" = %s AND "userID" = %s
            """,
            (new_quantity, cart_item_id, user.id)  # ← cart_item_id гэж өөрчил
        )

        if updated == 0:
            return Response({"error": "Энэ хоол таны сагсанд байхгүй"}, status=404)

        return Response({"message": "Тоо амжилттай шинэчлэгдлээ"}, status=200)
class CartItemDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, cart_item_id):  # ← ЭНД cart_item_id гэж өөрчил
        user = request.user
        
        if user.user_type != 'customer':
            return Response({"error": "Зөвхөн customer устгах боломжтой"}, status=403)

        deleted = execute_update(
            """
            DELETE FROM tbl_cart_food 
            WHERE "foodID" = %s AND "userID" = %s
            """,
            (cart_item_id, user.id)  # ← cart_item_id гэж өөрчил
        )

        if deleted == 0:
            return Response({"error": "Энэ хоол таны сагсанд байхгүй"}, status=404)

        return Response({"message": "Сагснаас устгагдлаа"}, status=204)
    