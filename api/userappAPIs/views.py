from datetime import datetime
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