from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import WorkerSerializer, SignInSerializer
from ..database import execute_query, execute_insert
from ..auth import hash_password, verify_password, create_access_token, JWTAuthentication
class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Check if worker exists
        existing_worker = execute_query(
            "SELECT workerID FROM tbl_worker WHERE email = %s OR phone = %s",
            (data['email'], data['phone']),
            fetch_one=True
        )
        
        if existing_worker:
            return Response(
                {'error': 'Имэйл эсвэл утасны дугаар аль хэдийн бүртгэлтэй байна'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Insert worker (password handling optional here if you plan to authenticate workers)
        worker = execute_insert(
            """
            INSERT INTO tbl_worker (workerName, phone, email, vehicleType, vehicleReg)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING workerID, workerName, phone, email, vehicleType, vehicleReg
            """,
            (
                data['workerName'],
                data['phone'],
                data['email'],
                data.get('vehicleType', None),
                data.get('vehicleReg', None)
            )
        )
        
        if not worker:
            return Response(
                {'error': 'Бүртгэл үүсгэхэд алдаа гарлаа'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': 'Амжилттай бүртгэгдлээ',
            'worker': worker
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