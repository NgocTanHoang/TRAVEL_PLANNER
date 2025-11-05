"""
Django settings for Vi Vu project.
Minimal production-ready configuration with SQLite for development.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # Go up one more level to project root

# Load environment variables from .env file
# Try loading with UTF-8 first, fallback to other encodings if needed
try:
    load_dotenv(PROJECT_ROOT / '.env', encoding='utf-8')  # Load from project root
except (UnicodeDecodeError, Exception):
    # If UTF-8 fails, try with error handling
    try:
        load_dotenv(PROJECT_ROOT / '.env', encoding='latin-1')
    except Exception:
        pass  # Continue if .env can't be loaded

try:
    load_dotenv(BASE_DIR / '.env', encoding='utf-8')  # Also try vivu_backend/.env (fallback)
except (UnicodeDecodeError, Exception):
    try:
        load_dotenv(BASE_DIR / '.env', encoding='latin-1')
    except Exception:
        pass

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-CHANGE-IN-PRODUCTION')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
# Allowed hosts: include LAN IP by default for local network access
# Django 4.0+ supports wildcard patterns starting with dot (.*) or asterisk (*)
allowed_hosts_default = 'localhost,127.0.0.1,192.168.1.3'
if DEBUG:
    # In debug mode, allow all ngrok domains
    allowed_hosts_default += ',.ngrok-free.app,.ngrok.io'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', allowed_hosts_default).split(',')

# CSRF Trusted Origins (required for POST/CSRF over HTTPS domains like ngrok)
# Note: Django supports wildcard patterns for CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.ngrok-free.app,https://*.ngrok.io,http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.users',
    'apps.places',
    'apps.itineraries',
    'apps.analytics',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vivu_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Add templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vivu_core.wsgi.application'

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Note: For production, use PostgreSQL:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME', 'vivu'),
#         'USER': os.getenv('DB_USER', 'postgres'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#     }
# }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom user model
AUTH_USER_MODEL = 'users.NguoiDung'

# Internationalization
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Add static directory
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'SEARCH_PARAM': 'q',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
}

# CORS
# Allow all origins in development for ngrok testing
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True') == 'True' if DEBUG else False
if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:8501,https://*.ngrok-free.app,https://*.ngrok.io'
    ).split(',')
CORS_ALLOW_CREDENTIALS = True

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Vi Vu API',
    'DESCRIPTION': 'Vietnamese Travel Planning Platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# AI/ML Integration (Optional - for future use)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# OpenRouteService API - For geocoding and routing
OPENROUTE_API_KEY = os.getenv('OPENROUTE_API_KEY', '')

# VietMap API - For geocoding and routing (preferred for Vietnam addresses)
# Get API key at: https://maps.vietmap.vn/ or contact: maps.info@vietmap.vn
VIETMAP_API_KEY = os.getenv('VIETMAP_API_KEY', '')

# Travelpayouts API (Optional - for flight and hotel prices)
TRAVELPAYOUTS_TOKEN = os.getenv('TRAVELPAYOUTS_TOKEN', '')

# FlightAPI.io (Optional - for flight prices)
FLIGHTAPI_KEY = os.getenv('FLIGHTAPI_KEY', '')

# OpenSky Network API (Optional - for flight tracking)
# OAuth2 Credentials (Preferred - Recommended)
OPENSKY_CLIENT_ID = os.getenv('OPENSKY_CLIENT_ID', '')
OPENSKY_CLIENT_SECRET = os.getenv('OPENSKY_CLIENT_SECRET', '')
# Basic Auth Credentials (Fallback)
OPENSKY_USERNAME = os.getenv('OPENSKY_USERNAME', '')
OPENSKY_PASSWORD = os.getenv('OPENSKY_PASSWORD', '')

# Tavily API (Optional - for web search and data enrichment)
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')

# SerpAPI (Optional - for Google Flights, Hotels, Restaurants search)
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY', '')

# Vector DB (Optional - for RAG)
VECTOR_DB_PATH = str(BASE_DIR / 'vector_db')

