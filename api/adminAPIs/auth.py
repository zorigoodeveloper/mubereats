import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password, make_password
from ..database import execute_query


def hash_password(password):
    """Hash password using Django make_password"""
    return make_password(password)


def verify_password(password, hashed):
    """Verify password using Django check_password"""
    return check_password(password, hashed)


def create_access_token(user_id, email):
    """Create JWT access token"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_access_token(token):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token has expired')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token')


class AuthUser(dict):
    @property
    def is_authenticated(self):
        return True
    @property
    def id(self):
        return self.get('id')
    @property
    def email(self):
        return self.get('email')


class JWTAuthentication(BaseAuthentication):
    """Custom JWT Authentication class"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None

            payload = decode_access_token(token)
            user_id = int(payload.get('user_id'))

            # auth_user хүснэгтээс админ хэрэглэгчийг авах
            user = execute_query(
                "SELECT * FROM auth_user WHERE id = %s AND is_active = TRUE",
                (user_id,),
                fetch_one=True
            )

            if not user:
                raise AuthenticationFailed('User not found')

            return (AuthUser(user), token)

        except (ValueError, AuthenticationFailed) as e:
            raise AuthenticationFailed(str(e))
    
    def authenticate_header(self, request):
        return 'Bearer'


