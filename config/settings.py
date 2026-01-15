import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
JWT_SECRET = os.getenv('JWT_SECRET')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.auth', 
    
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'api',
    'cloudinary',
    'cloudinary_storage',
]
import os

# Media файлуудын тохиргоо
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Хэрэгтэй бол дараахыг нэмнэ
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB

# Зургийн формат
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


import os
from dotenv import load_dotenv

load_dotenv()  

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', 'dvfclibsn'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', '219282487814685'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', 'Cy-y1hNCUTsAoKOCOpEl__hGwp8'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dvfclibsn',
    'API_KEY': '219282487814685',
    'API_SECRET': 'Cy-y1hNCUTsAoKOCOpEl__hGwp8',
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

# Database configuration for raw SQL
DATABASE_CONFIG = {
    'url': os.getenv('DATABASE_URL')
}

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny'
        # 'rest_framework.permissions.IsAuthenticated'
    ),
}


# CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_ALL_ORIGINS = True       
# CORS_ORIGIN_ALLOW_ALL = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ulaanbaatar'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME = 3600  # 1 hour in seconds