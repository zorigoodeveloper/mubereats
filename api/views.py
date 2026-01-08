from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import SignUpSerializer, SignInSerializer
from .database import execute_query, execute_insert
from .auth import hash_password, verify_password, create_access_token, JWTAuthentication

class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Check if user exists
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
        
        # Hash password
        password_hash = hash_password(data['password'])
        
        # Insert user
        user = execute_insert(
            """
            INSERT INTO users (email, phone_number, password_hash, full_name, user_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, email, phone_number, full_name, user_type, is_active, is_verified, created_at
            """,
            (data['email'], data['phone_number'], password_hash, data['full_name'], data['user_type'])
        )
        
        if not user:
            return Response(
                {'error': 'Бүртгэл үүсгэхэд алдаа гарлаа'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create profile based on user type
        if data['user_type'] == 'driver':
            execute_insert(
                """
                INSERT INTO driver_profiles (user_id, license_number, vehicle_type, vehicle_plate)
                VALUES (%s, %s, %s, %s)
                """,
                (user['id'], data.get('license_number', ''), data.get('vehicle_type', ''), data.get('vehicle_plate', ''))
            )
        elif data['user_type'] == 'customer':
            execute_insert(
                """
                INSERT INTO customer_profiles (user_id, default_address, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                """,
                (user['id'], data.get('default_address'), data.get('latitude'), data.get('longitude'))
            )
        
        # Create access token
        access_token = create_access_token(user['id'], user['email'])
        
        return Response({
            'message': 'Амжилттай бүртгэгдлээ',
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'phone_number': user['phone_number'],
                'full_name': user['full_name'],
                'user_type': user['user_type'],
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
        
        # Get user
        user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (data['email'],),
            fetch_one=True
        )
        
        if not user:
            return Response(
                {'error': 'Имэйл эсвэл нууц үг буруу байна'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not verify_password(data['password'], user['password_hash']):
            return Response(
                {'error': 'Имэйл эсвэл нууц үг буруу байна'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if active
        if not user['is_active']:
            return Response(
                {'error': 'Таны бүртгэл идэвхгүй байна'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create access token
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


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        profile_data = None
        if user['user_type'] == 'driver':
            profile_data = execute_query(
                "SELECT * FROM driver_profiles WHERE user_id = %s",
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
            'profile': profile_data
        })