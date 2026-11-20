"""Settings for the ALX Travel App. Values come from environment variables or a .env file."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-only-change-me')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    # Local apps
    'listings',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'alx_travel_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'alx_travel_app.wsgi.application'

# MySQL when DB_NAME is set (see .env.example), otherwise SQLite for local development
if env('DB_NAME', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER', default='root'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='3306'),
        }
    }
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000'])

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {'basic': {'type': 'basic'}},
    'USE_SESSION_AUTH': True,
}

# Chapa payment gateway (https://developer.chapa.co)
CHAPA_SECRET_KEY = env('CHAPA_SECRET_KEY', default='')
CHAPA_BASE_URL = env('CHAPA_BASE_URL', default='https://api.chapa.co/v1')
# Where Chapa sends the user after paying; it should point at /api/payments/verify/
CHAPA_RETURN_URL = env('CHAPA_RETURN_URL', default='http://localhost:8000/api/payments/verify/')

# Celery with RabbitMQ (run: celery -A alx_travel_app worker -l info)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='amqp://guest:guest@localhost:5672//')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='rpc://')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BROKER_CONNECTION_TIMEOUT = 3
CELERY_TASK_PUBLISH_RETRY = False

# Email: printed to the console unless SMTP settings are provided
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='ALX Travel App <no-reply@alxtravel.local>')
