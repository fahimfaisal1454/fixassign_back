import os
from pathlib import Path
from datetime import timedelta

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Core security & debug
# -------------------------------------------------------------------
# NOTE: Replace this in production and keep it out of version control.
SECRET_KEY = 'django-insecure-%h$alzm(49!l8vf#@c9-!-dslf!8pubj^jcy2u-9*9+pkfer5u'

# Set to False in production
DEBUG = True

ALLOWED_HOSTS = [
    'satighatass.edu.bd',
    'www.satighatass.edu.bd',
    '84.247.187.137',
    '127.0.0.1',
    'localhost',
]

# -------------------------------------------------------------------
# Installed apps
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'authentication',
    'institution.apps.InstitutionConfig',
    'people',
    'academics',
    'contact',
    'master',
    'acknowledgments',

    # Third-party
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
]

# -------------------------------------------------------------------
# Middleware
# Order matters: CORS should be high and before CommonMiddleware
# -------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'corsheaders.middleware.CorsMiddleware',   # <= keep high, before CommonMiddleware
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------------------------------------------
# URL / WSGI
# -------------------------------------------------------------------
ROOT_URLCONF = 'abdulgafur_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Add your template dirs if needed
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'abdulgafur_backend.wsgi.application'

# -------------------------------------------------------------------
# Database (SQLite by default)
# -------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# -------------------------------------------------------------------
# Auth / Users
# -------------------------------------------------------------------
AUTH_USER_MODEL = 'authentication.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# -------------------------------------------------------------------
# DRF & JWT
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=100),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
}

# -------------------------------------------------------------------
# I18N / TZ
# -------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'        # Change to 'Asia/Dhaka' if you prefer local time on the server
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & Media
# -------------------------------------------------------------------
STATIC_URL = '/static/'
# In production, collect static files here: `python manage.py collectstatic`
STATIC_ROOT = BASE_DIR / 'staticfiles'
# If you also keep app-level static during development, you can add:
# STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------------------------
# CORS / CSRF
# -------------------------------------------------------------------
# Frontend origins (Vite dev and production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://satighatass.edu.bd",
    "https://www.satighatass.edu.bd",
    "http://satighatass.edu.bd",     # if you ever serve http
    "http://www.satighatass.edu.bd", # if you ever serve http
]
CORS_ALLOW_CREDENTIALS = True

# CSRF requires schemes in Django 4+ (and 5+)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://satighatass.edu.bd",
    "https://www.satighatass.edu.bd",
    "http://satighatass.edu.bd",
    "http://www.satighatass.edu.bd",
]

# -------------------------------------------------------------------
# Optional: Security headers for production (enable when DEBUG=False)
# -------------------------------------------------------------------
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
