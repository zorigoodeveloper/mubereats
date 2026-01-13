import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .database import execute_query

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
            user_id = payload.get('user_id')
            
            # Check if user_id is UUID (for users table) or Integer (for tbl_worker)
            try:
                uuid.UUID(str(user_id))
                is_uuid = True
            except ValueError:
                is_uuid = False

            if is_uuid:
                # Get user from database
                user = execute_query(
                    "SELECT * FROM users WHERE id = %s AND is_active = TRUE",
                    (user_id,),
                    fetch_one=True
                )
            else:
                # Get worker from database
                user = execute_query(
                    'SELECT * FROM "tbl_worker" WHERE "workerID" = %s',
                    (user_id,),
                    fetch_one=True
                )
                if user:
                    user['id'] = user['workerID']
            
            if not user:
                raise AuthenticationFailed('User not found')
                
            return (AuthUser(user), token)
            
        except (ValueError, AuthenticationFailed) as e:
            raise AuthenticationFailed(str(e))
    
    def authenticate_header(self, request):
        return 'Bearer'
