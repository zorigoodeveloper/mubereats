from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers import SignUpSerializer, SignInSerializer
from ..database import execute_query, execute_insert, execute_update
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication

# ====== ХЭРЭГЛЭГЧЭЭР БҮРТГҮҮЛЭХ ======
class CustomerSignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Хэрэглэгчийн талбаруудыг валидаци хийх
        required_fields = ['email', 'phone_number', 'full_name', 'password']
        optional_fields = ['default_address', 'latitude', 'longitude']

        data = request.data

        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'{field} талбарыг заавал оруулна уу'}, status=status.HTTP_400_BAD_REQUEST)

        # Имэйл эсвэл утас давхардаж байгаа эсэх
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s OR phone_number = %s",
            (data['email'], data['phone_number']),
            fetch_one=True
        )
        if existing_user:
            return Response(
                {'error': 'Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Нууц үг hash
        password_hash = hash_password(data['password'])

        # Хэрэглэгч үүсгэх
        user = execute_insert(
            """
            INSERT INTO users (email, phone_number, password_hash, full_name, user_type)
            VALUES (%s, %s, %s, %s, 'customer')
            RETURNING id, email, phone_number, full_name, user_type, is_active, is_verified, created_at
            """,
            (data['email'], data['phone_number'], password_hash, data['full_name'])
        )

        if not user:
            return Response({'error': 'Бүртгэл үүсгэхэд алдаа гарлаа'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Customer profile үүсгэх
        execute_insert(
            """
            INSERT INTO customer_profiles (user_id, default_address, latitude, longitude)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user['id'],
                data.get('default_address'),
                data.get('latitude'),
                data.get('longitude')
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

    def patch(self, request):
        user = request.user
        data = request.data

        if not data:
            return Response({'message': 'Өөрчлөх талбар оруулаагүй байна'}, status=status.HTTP_200_OK)

        updated = False

        # 1. users хүснэгтэд нийтлэг талбарууд
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
            values.append(str(user['id']))  # UUID-г string болго

            execute_update(
                f"UPDATE users SET {set_clause} WHERE id = %s",
                tuple(values)
            )

        # 2. Customer profile
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
    
